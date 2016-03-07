#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################
"""
:author:
    Guannan Ma
:create_date:
    2014
<<<<<<< HEAD
:last_date:
    2014
:descrition:
    connection related module
=======
:last_modify_date:
    2015.6.29
:descrition:
    connection related module

    1. There's only 1 thread reading/receiving data from the interface.

    2. There might have more than 1 thred writing data into the network
       queue. 1 thread per context(ip, port).

    Notice that _do_write will only TRY to send out some data. It might
    encounter TCP/IP stack full of data in the send queue of
    the network interface
>>>>>>> origin/master
"""

import copy
import socket
import select
import errno
import threading
try:
    import Queue as queue  # pylint: disable=F0401
except ImportError:
    import queue   # pylint: disable=F0401

import cup
from cup.util import misc
from cup.util import threadpool
from cup.net.async import msg as async_msg


__all__ = [
    'CConnContext',
    'CConnectionManager',
]


def _try_get_peer_info(sock):
    try:
        peer = sock.getpeername()
    except socket.error as error:
        peer = ('Error happened', str(error))
    except Exception as error:
        peer = ('_try_get_peer_info error happend', str(error))

    return peer


class CConnContext(object):  # pylint: disable=R0902
    """
    Connection上下文处理类
    """
    def __init__(self):
        self._destroying = False
        self._sock = None
        self._peerinfo = None

        self._sending_msg = None
        self._send_queue = queue.PriorityQueue(0)
        self._recving_msg = None
        self._msgind_in_sendque = 0
        self._is_reading = None
        self._is_1st_recv_msg = True
        self._is_1st_send_msg = True

        self._conn = None

        self._lock = threading.Lock()
        self._readlock = threading.Lock()
        self._writelock = threading.Lock()

    def __del__(self):
        pass

    def to_destroy(self):
        """
        destroy context
        """
        self._lock.acquire()
        self._destroying = True
        if self._sock is None:
            msg = 'context is with no sock'
        else:
            msg = 'context with socket: %s' % str(self._sock)
        cup.log.debug('to destroy context, ' + msg)
        self._lock.release()

    def is_detroying(self):
        """
        is context being destroyed
        """
        self._lock.acquire()
        is_destryoing = self._destroying
        self._lock.release()
        return is_destryoing

    def set_conn_man(self, conn):
        """
        set conn for context
        """
        cup.log.debug('set conn:%s' % str(conn))
        self._conn = conn

    def set_sock(self, sock):
        """
        associate socket
        """
        self._lock.acquire()
        self._sock = copy.copy(sock)
        self._lock.release()

    def get_sock(self):
        """
        return associated socket
        """
        misc.check_not_none(self._sock)
        sock = self._sock
        return sock

    def do_recv_data(self, data, data_len):
        """
        push data into the recving_msg queue
        network read should be in 1 thread only.
        """
        if self._recving_msg is None:
            raise cup.err.NotInitialized('self._recving_msg')
        ret = self._recving_msg.push_data(data)
        #  cup.log.debug('pushed data length: %d' % ret)
        if data_len >= ret:
            if self._recving_msg.is_recvmsg_complete():
                cup.log.info(
                    'get a msg: msg_type:ACK, msg_len:%d, msg_flag:%d,'
                    'msg_src:%s, msg_dest:%s, uniqid:%d' %
                    (
                        self._recving_msg.get_msg_len(),
                        self._recving_msg.get_flag(),
                        str(self._recving_msg.get_from_addr()),
                        str(self._recving_msg.get_to_addr()),
                        self._recving_msg.get_uniq_id()
                    )
                )
                self._conn.get_recv_queue().put(
                    (self._recving_msg.get_flag(), self._recving_msg)
                )
                self._recving_msg = self.get_recving_msg()
            #  the pushed data should span on two msg datas
            if data_len > ret:
                return self.do_recv_data(data[ret:], (data_len - ret))
        else:
            cup.log.critical(
                'Socket error. We cannot get more than pushed data length'
            )
            assert False
        return

    def get_recving_msg(self):
        """
        get the net msg being received
        """
        cup.log.debug('to get recving_msg')
        #  if no recving msg pending there, create one.
        if self._recving_msg is None:
            self._recving_msg = async_msg.CNetMsg(is_postmsg=False)

        if self._recving_msg.is_recvmsg_complete():
            self._recving_msg = async_msg.CNetMsg(is_postmsg=False)

        if self._is_1st_recv_msg:
            self._recving_msg.set_need_head(True)
            self._is_1st_recv_msg = False
        else:
            self._recving_msg.set_need_head(False)

        msg = self._recving_msg
        return msg

    def try_move2next_sending_msg(self):
        """
        move to next msg that will be sent
        """
        if self._sending_msg is None or \
                self._sending_msg.is_msg_already_sent():
            cup.log.debug('to move2next_sending_msg')
            # if self._sending_msg is not None:
            #     # del self._sending_msg
            #     pass
            try:
                item = self._send_queue.get_nowait()
                msg = item[2]
            except queue.Empty:
                cup.log.debug('The send queue is empty')
                msg = None
            except Exception as error:
                errmsg = (
                    'Catch a error that I cannot handle, err_msg:%s' %
                    str(error)
                )
                cup.log.critical(errmsg)
                # self._lock.release()
                raise CConnectionManager.QueueError(errmsg)
            self._sending_msg = msg
        else:
            cup.log.debug(
                'No need to move to next msg since the current one'
                'is not sent out yet'
            )
        temp = self._sending_msg
        return temp

    def put_msg(self, flag, msg):
        """
        Put msg into the sending queue.

        :param flag:
            flag determines the priority of the msg.

            Msg with higher priority will have bigger chance to be

            sent out soon.

        :TODO:
            If the msg queue is too big, consider close the network link
        """
        self._lock.acquire()
        if self._is_1st_send_msg:
            msg.set_need_head(True)
            # pylint: disable=W0212
            msg._set_msg_len()
            self._is_1st_send_msg = False
        else:
            msg.set_need_head(False)
            cup.log.debug(
                'put msg into context, msg_type:ACK, msg_flag:%d,'
                'msg_src:%s, msg_dest:%s, uniqid:%d' %
                (
                    msg.get_flag(),
                    str(msg.get_from_addr()),
                    str(msg.get_to_addr()),
                    msg.get_uniq_id()
                )
            )
            # pylint: disable=W0212
            msg._set_msg_len()
        self._send_queue.put((flag, self._msgind_in_sendque, msg))
        self._msgind_in_sendque += 1
        self._lock.release()

    def get_context_info(self):
        """
        get context info
        """
        peerinfo = self.get_peerinfo()
        msg = 'Peer socket(%s:%s).' % (peerinfo[0], peerinfo[1])
        return msg

    def set_reading(self, is_reading):
        """
        set reading status
        """
        self._lock.acquire()
        self._is_reading = is_reading
        self._lock.release()

    def is_reading(self):
        """
        get if it is reading
        """
        self._lock.acquire()
        is_reading = self._is_reading
        self._lock.release()
        return is_reading

    def try_readlock(self):
        """
        try to acquire readlock

        :return:
            True if succeed. False, otherwise
        """
        return self._readlock.acquire(False)

    def release_readlock(self):
        """
        release the readlock
        """
        self._readlock.release()

    def try_writelock(self):
        """
        :return:
            True if succeed. False, otherwise
        """
        return self._writelock.acquire(False)

    def release_writelock(self):
        """
        release the writelock
        """
        self._writelock.release()

    def set_peerinfo(self, peer):
        """
        set peerinfo
        """
        if type(peer) != tuple:
            raise ValueError('peer is not a tuple')
        self._peerinfo = peer

    def get_peerinfo(self):
        """
        get peerinfo
        """
        return self._peerinfo


# pylint: disable=R0902
class CConnectionManager(object):
    """
        connaddr. Convert ip:port  into a 64-bit hex.

    """
    NET_RW_SIZE = 131072

    class QueueError(Exception):
        """
        internal queue error for CConnectionManager class
        """
        def __init__(self, msg):
            super(self.__class__, self).__init__()
            self._msg = msg

        def __repr__(self):
            return self._msg

    def __init__(self, ip, bindport, thdpool_param):
        #  TODO: Close idle socket after 30 mins with no data sent or received.
        self._conns = {}
        self._bind_port = bindport
        self._bind_ip = ip
        self._epoll = select.epoll()
        self._stopsign = False
        self._bind_sock = None
        self._fileno2context = {}
        self._context2fileno_peer = {}
        self._peer2context = {}
        #  self._kp_params = keepalive_params

        min_thds, max_thds = thdpool_param
        self._thdpool = threadpool.ThreadPool(min_thds, max_thds)
        self._recv_queue = queue.PriorityQueue(0)
        self._stopsign = False

        self._recv_msg_ind = 0

    @classmethod
    def _set_sock_params(cls, sock):
        cup.net.set_sock_keepalive_linux(sock, 1, 3, 3)
        cup.net.set_sock_linger(sock)
        cup.net.set_sock_quickack(sock)
        cup.net.set_sock_reusable(sock, True)

    @classmethod
    def _set_sock_nonblocking(cls, sock):
        sock.setblocking(0)

    @classmethod
    def _epoll_write_params(cls):
        return (select.EPOLLET | select.EPOLLOUT | select.EPOLLERR)

    @classmethod
    def _epoll_read_params(cls):
        return (select.EPOLLET | select.EPOLLIN | select.EPOLLERR)

    def bind(self):
        """
        bind the ip:port
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._set_sock_params(sock)
        sock.bind((self._bind_ip, self._bind_port))
        self._set_sock_nonblocking(sock)
        cup.log.info(
            'bind info:(ip:%s, port:%s)' % (
                self._bind_ip, self._bind_port
            )
        )
        self._epoll.register(
            sock.fileno(),
            select.EPOLLIN | select.EPOLLET | select.EPOLLOUT | select.EPOLLERR
        )
        self._bind_sock = sock

    def push_msg2sendqueue(self, msg):
        """
        push msg into the send queue
        """
        if msg is None:
            cup.log.warn('put a None into msg send queue. return')
            return
        flag = msg.get_flag()
        #  cup.log.debug('to put flag and msg into the queue. flag:%d' % flag)
        #  self._send_queue.put( (flag, msg) )
        peer = msg.get_to_addr()[0]
        new_created = False
        context = None
        if peer not in self._peer2context:
            cup.log.info('To create a new context for the sock')
            # if the connection has not been established
            sock = self.connect(peer)
            if sock is not None:
                context = CConnContext()
                context.set_conn_man(self)
                context.set_sock(sock)
                context.set_peerinfo(peer)
                fileno = sock.fileno()
                self._peer2context[peer] = context
                self._fileno2context[fileno] = context
                self._context2fileno_peer[context] = (fileno, peer)
                new_created = True
                cup.log.info('created context for the new sock')
                new_created = True
            else:
                cup.log.critical(
                    'failed to post msg as the socket.connect failed'
                )
        else:
            context = self._peer2context[peer]
        context.put_msg(flag, msg)
        if new_created:
            try:
                self._epoll.register(sock.fileno(), self._epoll_write_params())
            except Exception as error:  # pylint: disable=W0703
                cup.log.warn(
                    'failed to register the socket fileno, err_msg:%s,'
                    'perinfo:%s:%s. To epoll modify it' %
                    (str(error), peer[0], peer[1])
                )
                self._epoll.modify(sock.fileno(), self._epoll_write_params())
        self._handle_new_send(context)

    def connect(self, peer):
        """
        :param peer:
            ip:port
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._set_sock_params(sock)
        try:
            sock.connect(peer)
            self._set_sock_nonblocking(sock)
            return sock
        except socket.error as error:
            cup.log.warn(
                'failed to connect to %s:%s. Error:%s' %
                (peer[0], peer[1], str(error))
            )
            return None
        else:
            return None

    def _handle_new_conn(self, newsock, peer):
        self._set_sock_params(newsock)
        self._set_sock_nonblocking(newsock)
        context = CConnContext()
        context.set_sock(newsock)
        context.set_conn_man(self)
        context.set_peerinfo(peer)
        self._epoll.register(
            newsock.fileno(), select.EPOLLIN | select.EPOLLET | select.EPOLLERR
        )
        self._fileno2context[newsock.fileno()] = context
        self._peer2context[peer] = context
        self._context2fileno_peer[context] = (newsock.fileno(), peer)
        cup.log.info('a new connection: %s:%s' % (peer[0], peer[1]))

    def _handle_error_del_context(self, context):
        peerinfo = context.get_peerinfo()
        cup.log.info(
            'handle socket error, to close the socket:%s:%s' %
            (peerinfo[0], peerinfo[1])
        )
        fileno_peer = self._context2fileno_peer[context]
        cup.log.info('socket info: %s' % str(fileno_peer[1]))
        try:
            sock = context.get_sock()
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            context.set_sock(None)
        except socket.error as error:
            cup.log.debug(
                'Failed to shutdown/close the socket, err_msg:%s' % str(error)
            )
        try:
            self._epoll.unregister(fileno_peer[0])
        except Exception as error:  # pylint: disable=W0703
            cup.log.warn(
                'epoll unregister error:%s, peerinfo:%s' %
                (str(error), str(fileno_peer[1]))
            )
        cup.log.info('Socket closed')
        del self._fileno2context[fileno_peer[0]]
        del self._peer2context[fileno_peer[1]]
        del self._context2fileno_peer[context]
        del context

    def poll(self):
        """
        start to poll
        """
        self._thdpool.start()
        misc.check_not_none(self._bind_sock)
        self._bind_sock.listen(10)
        while not self._stopsign:
            try:
                events = self._epoll.poll(1)
            except IOError as err:
                if err.errno == errno.EINTR:
                    return
                raise err
            # cup.log.debug('start to poll')
            for fileno, event in events:
                # if it comes from the listen port, new conn
                if fileno == self._bind_sock.fileno():
                    newsock, addr = self._bind_sock.accept()
                    cup.log.debug(
                        'epoll catch a new connection: %s:%s' %
                        (addr[0], addr[1])
                    )
                    self._handle_new_conn(newsock, addr)
                elif event & select.EPOLLIN:
                    try:
                        self._handle_new_recv(self._fileno2context[fileno])
                    except KeyError:
                        cup.log.info('socket already closed')
                elif event & select.EPOLLOUT:
                    try:
                        self._handle_new_send(self._fileno2context[fileno])
                    except KeyError:
                        cup.log.info('socket already closed')
                elif (event & select.EPOLLHUP) or (event & select.EPOLLERR):
                    if event & select.EPOLLHUP:
                        cup.log.info('--EPOLLHUP--')
                    else:
                        cup.log.info('--EPOLLERR--')
                    try:
                        self._handle_error_del_context(
                            self._fileno2context[fileno]
                        )
                    except KeyError:
                        cup.log.info('socket already closed')

    def dump_stats(self):
        """
        dump stats
        """
        self._thdpool.dump_stats()

    def stop(self):
        """
        stop the connection manager
        """
        cup.log.info('to stop the connection manager')
        self._stopsign = True
        self._thdpool.stop()
        cup.log.info('connection manager stopped')

    def get_recv_msg_ind(self):
        """
        get recv msg ind
        """
        tmp = self._recv_msg_ind
        self._recv_msg_ind += 1
        return tmp

    def get_recv_queue(self):
        """
        get recving_msg queue
        """
        return self._recv_queue

    def get_recv_msg(self):
        """
        get recv msg from queue
        """
        cup.log.debug('to fetch a msg from recv_queue for handle function')
        try:
            msg = self._recv_queue.get(True, 2)[1]
        except queue.Empty as error:
            cup.log.debug('The recv queue is empty')
            msg = None
        except Exception as error:
            msg = 'Catch a error that I cannot handle, err_msg:%s' % str(error)
            cup.log.critical(msg)
            raise CConnectionManager.QueueError(msg)
        return msg

    def _handle_new_recv(self, context):
        self.read(context)

    def _finish_read_callback(self, succ, result):
        context = result
        cup.log.debug(
            'context:%s, succ:%s' % (context.get_context_info(), succ)
        )

        if context.is_detroying():
            # destroy the context and socket
            context.release_readlock()
            self._handle_error_del_context(context)
        else:
            self._epoll.modify(
                context.get_sock().fileno(), select.EPOLLIN | select.EPOLLET
            )
            context.release_readlock()

    def read(self, context):
        """
        read with conn context
        """
        if context.is_detroying():
            cup.log.debug('The context is being destroyed. return')
            return
        if not context.try_readlock():
            return

        cup.log.debug(
            'succeed to acquire readlock, to add the \
            readjob into the threadpool'
        )
        try:
            self._do_read(context)
            self._finish_read_callback(True, context)
        except Exception as error:
            self._finish_read_callback(False, context)

    def _do_read(self, context):
        # cup.log.debug('enter _do_read')
        sock = context.get_sock()
        data = ''
        context.get_recving_msg()
        while self._stopsign is not True:
            try:
                data = sock.recv(self.NET_RW_SIZE)
            except socket.error as error:
                err = error.args[0]
                if err == errno.EAGAIN:
                    cup.log.info(
                        'EAGAIN happend, peer info %s' %
                        context.get_context_info()
                    )
                    return context
                elif err == errno.EWOULDBLOCK:
                    cup.log.info(
                        'EWOULDBLOCK happend, context info %s' %
                        context.get_context_info()
                    )
                    return context
                else:
                    cup.log.warn(
                        'Socket error happend, error:%s,  peer info %s' %
                        (str(error), context.get_context_info())
                    )
                    context.to_destroy()
                    return context
            except Exception as error:
                cup.log.critical(
                    'Socket error happend, error:%s,  peer info %s' %
                    (str(error), context.get_context_info())
                )
                context.to_destroy()
                return context
            data_len = len(data)
            if data_len == 0:
                # socket closed by peer
                context.to_destroy()
                return context
            context.do_recv_data(data, data_len)

    def _finish_write_callback(self, succ, result):
        context = result
        cup.log.debug(
            'context:%s, succ:%s' % (context.get_context_info(), succ)
        )
        # You cannot do things below as getpeername will block if the conn
        # has problem!!!!!   - Guannan
        # try:
        #     context.get_sock().getpeername()
        # except socket.error as error:
        #   cup.log.debug('Seems socket failed to getpeername:%s' % str(error))
        #   context.to_destroy()
        if context.is_detroying():
            # destroy the context and socket
            context.release_writelock()
            self._handle_error_del_context(context)
        else:
            cup.log.debug('to epoll modify')
            epoll_write_params = self._epoll_write_params()
            context.release_writelock()

    # context hash locked the writing.
<<<<<<< HEAD
    # guarantee there's only 1 thread for context reading.
=======
    # guarantee there's only 1 thread for context writing.
>>>>>>> origin/master
    def _handle_new_send(self, context):
        self.add_write_job(context)

    def _do_write(self, context):
        sock = context.get_sock()
        msg = context.try_move2next_sending_msg()
        if msg is None:
            cup.log.debug('send queue is empty, quit the _do_write thread')
            return context
        cup.log.debug('To enter write loop until eagin')
        # pylint:disable=w0212
        # cup.log.debug('This msg _need_head:%s' % msg._need_head)
        while not self._stopsign:
            data = msg.get_write_bytes(self.NET_RW_SIZE)
            cup.log.debug('get_write_bytes_len: %d' % len(data))
            try:
                succ_len = sock.send(data)
                # cup.log.debug('succeed to send length:%d' % succ_len)
                msg.seek_write(succ_len)
            except socket.error as error:
                err = error.args[0]
                if err == errno.EAGAIN:
                    cup.log.debug(
                        'EAGAIN happend, context info %s' %
                        context.get_context_info()
                    )
                    return context
                elif err == errno.EWOULDBLOCK:
                    cup.log.debug(
                        'EWOULDBLOCK happend, context info %s' %
                        context.get_context_info()
                    )
                    return context
                else:
                    cup.log.warn(
                        'Socket error happend. But its not eagin,error:%s,\
                        context info %s, errno:%s' %
                        (str(error), context.get_context_info(), err)
                    )
                    context.to_destroy()
                    break
            except Exception as error:
                cup.log.critical(
                    'Socket error happend, error:%s,  context info %s' %
                    (str(error), context.get_context_info())
                )
                context.to_destroy()
                break
            cup.log.debug('%d bytes has been sent' % succ_len)
            if msg.is_msg_already_sent():
                cup.log.info(
                    'send out a msg: msg_type:ACK, msg_len:%d, msg_flag:%d, \
                    msg_src:%s, msg_dest:%s, uniqid:%d' %
                    (
                        msg.get_msg_len(),
                        msg.get_flag(),
                        str(msg.get_from_addr()),
                        str(msg.get_to_addr()),
                        msg.get_uniq_id()
                    )
                )
                del msg
                # if we have successfully send out a msg. Then move to next one
                msg = context.try_move2next_sending_msg()
                if msg is None:
                    break
        return context

    def add_write_job(self, context):
        """
        add network write into queue
        """
        peerinfo = context.get_peerinfo()
        if not context.try_writelock():
            cup.log.debug(
<<<<<<< HEAD
                'Another thread is reading the context. Peerinfo:%s:%s' %
=======
                'Another thread is writing the context, return. Peerinfo:%s:%s' %
>>>>>>> origin/master
                (peerinfo[0], peerinfo[1])
            )
            return
        if context.is_detroying():
            cup.log.debug(
                'The context is being destroyed, i will do nothing. '
                'Peerinfo:%s:%s' %
                (peerinfo[0], peerinfo[1])
            )
            return
        try:
            self._do_write(context)
            self._finish_write_callback(True, context)
        # pylint: disable=W0703
        except Exception as error:
            cup.log.debug(
                'seems error happend for context:%s Peerinfo:%s:%s' %
                (str(error), peerinfo[0], peerinfo[1])
            )
            self._finish_write_callback(False, context)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
