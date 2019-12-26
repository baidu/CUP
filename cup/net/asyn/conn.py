#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma
"""
:descrition:
    connection related module

    1. There's only 1 thread reading/receiving data from the interface.

    2. There might have more than 1 thred writing data into the network
       queue. 1 thread per context(ip, port).

    Notice that _do_write will only TRY to send out some data. It might
    encounter TCP/IP stack full of data in the SEND buffer-queue of
    the network interface
"""
import socket
import select
import errno
import time
import threading
import traceback
try:
    import Queue as queue  # pylint: disable=F0401
except ImportError:
    import queue   # pylint: disable=F0401

import cup
from cup import log
from cup import err as cuperr
from cup.util import misc
from cup.util import threadpool
from cup.services import executor
from cup.net.asyn import msg as async_msg
from cup.net.asyn import context as sockcontext


__all__ = [
    'CConnectionManager'
]


def _try_get_peer_info(sock):
    """
    get peer info
    """
    try:
        peer = sock.getpeername()
    except socket.error as error:
        peer = ('Error happened', str(error))
    except Exception as error:
        peer = ('_try_get_peer_info error happend', str(error))
    return peer


# pylint: disable=R0902
class CConnectionManager(object):
    """
        connaddr. Convert ip:port  into a 64-bit hex.
    """
    NET_RW_SIZE = 131072
    # NET_RW_SIZE = 4096

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
        min_thds, max_thds = thdpool_param
        self._thdpool = threadpool.ThreadPool(
            min_thds, max_thds, name='network_write_read')
        self._recv_queue = queue.PriorityQueue(0)
        self._stopsign = False
        self._recv_msg_ind = 0
        self._mlock = threading.Lock()
        # _needack_context_queue
        # infinite queue  TODO:  may change it in the future
        self._needack_context_queue = queue.Queue()
        self._dict_lock = threading.Lock()
        self._needack_context_dict = {}
        self._executor = executor.ExecutionService(
            #int('queue_exec_thdnum'),    # todo num?
            #int('queue_delay_exe_thdnum')   # todo num?
            3,
            4
        )
        self._type_man = async_msg.CMsgType()
        self._type_man.register_types(async_msg.MSG_TYPE2NUM)

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

    def get_needack_dict(self):
        """
        get neekack dict
        """
        return self._needack_context_dict

    def push_msg2needack_queue(self, msg):
        """
        get neekack dict
        """
        log.debug('push ack ok msg into needack_queue.')
        self._needack_context_queue.put(msg)

    def bind(self):
        """
        bind the ip:port
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._set_sock_params(sock)
        sock.bind((self._bind_ip, self._bind_port))
        self._set_sock_nonblocking(sock)
        log.info(
            'bind port info:(ip:%s, port:%s)' % (
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
        ret = 0
        if msg is None:
            log.warn('put a None into msg send queue. return')
            ret = -1
            return ret
        valid, errmsg = msg.is_valid4send(msg)
        if not valid:
            log.error('failed to send msg as msg is not valid to send')
            return -1
        flag = msg.get_flag()
        peer = msg.get_to_addr()[0]
        new_created = False
        context = None
        sock = None
        if isinstance(msg, async_msg.CNeedAckMsg):
            log.debug('CNeedAckMsg is to be sent. msg_type:%d,'
                'msg_flag:%d, msg_dest:%s, uniqid:%d' %
                (
                    msg.get_msg_type(),
                    msg.get_flag(),
                    str(msg.get_to_addr()),
                    msg.get_uniq_id()
                )
            )
            # no need head by default
            # msg.set_need_head(b_need=False)
            if msg.get_last_retry_time() is None:
                msg.set_last_retry_time(time.time())
            # if not in the self._needack_context_dict
            if msg.get_retry_times() <= 0:
                self._needack_context_queue.put(msg)
        try:
            context = self._peer2context[peer]
        except KeyError:
            log.info('To create a new context for the sock:{0}'.format(
                peer)
            )
            self._mlock.acquire()
            if peer not in self._peer2context:
                sock = self.connect(peer)
                if sock is not None:
                    context = sockcontext.CConnContext()
                    context.set_conn_man(self)
                    context.set_sock(sock)
                    context.set_peerinfo(peer)
                    fileno = sock.fileno()
                    self._peer2context[peer] = context
                    self._fileno2context[fileno] = context
                    self._context2fileno_peer[context] = (fileno, peer)
                    ret = 0
                    try:
                        self._epoll.register(
                            sock.fileno(), self._epoll_write_params()
                        )
                    except Exception as error:  # pylint: disable=W0703
                        log.warn(
                            'failed to register the socket fileno, err_msg:%s,'
                            'perinfo:%s:%s. To epoll modify it' %
                            (str(error), peer[0], peer[1])
                        )
                        self._epoll.modify(
                            sock.fileno(), self._epoll_write_params()
                        )
                else:
                    log.error(
                        'failed to post msg. Connect failed. peer info:{0}.'
                        ' msg_type:{1}'.format(
                            str(peer), msg.get_msg_type()
                        )
                    )
                    ret = -1
            else:
                context = self._peer2context[peer]
            self._mlock.release()
        else:
            context = self._peer2context[peer]
        if ret != 0:
            return ret
        if not context.is_detroying():
            if context.put_msg(flag, msg) == 0:
                ret = 0
                # set up last modify
            else:
                ret = -1
            log.debug('start handle new send.')
            self._handle_new_send(context)
            return ret

    def connect(self, peer):
        """
        :param peer:
            ip:port
        """
        log.info('to connect to peer:{0}'.format(peer))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._set_sock_params(sock)
        try:
            ret = sock.connect_ex(peer)
            if ret != 0:
                log.warn('connect failed, peer:{0}'.format(peer))
                return None
            if sock.getpeername() == sock.getsockname():
                log.warn('connect failed, seems connected to self')
                sock.close()
                return None
            self._set_sock_nonblocking(sock)
            return sock
        except socket.error as error:
            log.warn(
                'failed to connect to %s:%s. Error:%s' %
                (peer[0], peer[1], str(error))
            )
            sock.close()
            return None
        else:
            sock.close()
            return None

    def _handle_new_conn(self, newsock, peer):
        self._mlock.acquire()
        self._set_sock_params(newsock)
        self._set_sock_nonblocking(newsock)
        context = sockcontext.CConnContext()
        context.set_sock(newsock)
        context.set_conn_man(self)
        context.set_peerinfo(peer)
        self._epoll.register(
            newsock.fileno(), select.EPOLLIN | select.EPOLLET | select.EPOLLERR
        )
        self._fileno2context[newsock.fileno()] = context
        self._peer2context[peer] = context
        self._context2fileno_peer[context] = (newsock.fileno(), peer)
        log.info('a new connection: %s:%s' % (peer[0], peer[1]))
        self._mlock.release()

    def cleanup_error_context(self, context):
        """clean up error context"""
        def _cleanup_context(send_queue, peerinfo):
            """cleanup context"""
            log.debug('to cleanup socket, peer:{0}'.format(peerinfo))
            log.debug(
                'cleanup: send_queue of socket size:{0}'.format(
                    send_queue.qsize()
                )
            )
            while True:
                try:
                    item = send_queue.get_nowait()
                    msg = item[2]
                    del msg
                except queue.Empty:
                    break
        if context is None:
            return
        self._mlock.acquire()
        try:
            peerinfo = context.get_peerinfo()
            log.info(
                'handle socket reset by peer, to close the socket:%s:%s' %
                (peerinfo[0], peerinfo[1])
            )
            fileno_peer = self._context2fileno_peer[context]
            try:
                sock = context.get_sock()
                sock.close()
                context.set_sock(None)
            except socket.error as error:
                log.info(
                    'failed to close the socket, err_msg:%s' % str(error)
                )
            except Exception as error:
                log.warn('failed to close socket:{0}'.format(error))
            try:
                self._epoll.unregister(fileno_peer[0])
            except Exception as error:  # pylint: disable=W0703
                log.warn(
                    'epoll unregister error:%s, peerinfo:%s' %
                    (str(error), str(fileno_peer[1]))
                )
            del self._fileno2context[fileno_peer[0]]
            del self._peer2context[fileno_peer[1]]
            del self._context2fileno_peer[context]
            log.info('socket {0} closed successfully'.format(peerinfo))
        except Exception as error:
            pass
        finally:
            self._mlock.release()
        # pylint: disable=W0212
        self._thdpool.add_1job(_cleanup_context, context._send_queue, peerinfo)
        listened_peer = context.get_listened_peer()
        if listened_peer is not None and (listened_peer in self._peer2context):
            log.info(
                'clean up socket: this socket has listened peer {0}, will'
                ' clean up it as well.'.format(listened_peer))
            self.cleanup_error_context(self._peer2context[listened_peer])

    def close_socket(self, msg, recv_socket):
        """
        close socket by msg
        """
        peer = None
        try:
            if not recv_socket:
                peer = msg.get_to_addr()[0]
            else:
                peer = msg.get_from_addr()[0]
            context = self._peer2context.get(peer)
            if context is not None:
                self.cleanup_error_context(context)
            else:
                log.warn('conn manager close socket failed:{0}'.format(
                    peer)
                )
        except Exception as err:
            log.warn('failed to close socket:{1}, recv_socket:{0}'.format(
                recv_socket, err)
            )
        return

    def poll(self):
        """
        start to poll
        """
        self._thdpool.start()
        self._executor.run()
        log.info('thdpool and executor start')
        misc.check_not_none(self._bind_sock)
        self._bind_sock.listen(10)
        self._executor.delay_exec(
            2,   # todo set the check_time to ?
            self.do_check_msg_ack_loop,
            urgency=executor.URGENCY_HIGH
        )
        while not self._stopsign:
            try:
                events = self._epoll.poll(1)
            except IOError as err:
                if err.errno == errno.EINTR:
                    return
                raise err
            # log.debug('start to poll')
            for fileno, event in events:
                # if it comes from the listen port, new conn
                if fileno == self._bind_sock.fileno():
                    newsock, addr = self._bind_sock.accept()
                    self._handle_new_conn(newsock, addr)
                elif event & select.EPOLLIN:
                    try:
                        self._handle_new_recv(self._fileno2context[fileno])
                    except KeyError:
                        log.info('socket already closed')
                elif event & select.EPOLLOUT:
                    try:
                        self._handle_new_send(self._fileno2context[fileno])
                    except KeyError:
                        log.info('socket already closed')
                elif (event & select.EPOLLHUP) or (event & select.EPOLLERR):
                    # FIXME: consider if we need to release net msg resources
                    if event & select.EPOLLHUP:
                        log.info('--EPOLLHUP--')
                    else:
                        log.info('--EPOLLERR--')
                    try:
                        self.cleanup_error_context(
                            self._fileno2context[fileno]
                        )
                    except KeyError:
                        log.info('socket already closed')

    def dump_stats(self):
        """
        dump stats
        """
        self._thdpool.dump_stats()

    def _async_stop(self, force_stop):
        """
        to async stop thread pool and executor"""
        stop_pool = threading.Thread(
            target=self._thdpool.stop, args=(force_stop, )
        )
        stop_pool.start()
        stop_executor = threading.Thread(
            target=self._executor.stop, args=(force_stop, )
        )
        stop_executor.start()
        stop_pool.join()
        stop_executor.join()

    def stop(self, force_stop=False):
        """
        stop the connection manager
        """
        log.info('to stop the connection manager')
        self._stopsign = True
        self._async_stop(force_stop)
        log.info('connection manager stopped')

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
        log.debug('to fetch a msg from recv_queue for handle function')
        try:
            # should use block-mode, othwersie the while loop in the upper
            # code scope will crazily occupy a full cpu-core capacity.
            msg = self._recv_queue.get(block=True, timeout=0.5)[1]
        except queue.Empty as error:
            msg = None
        except TypeError as error:
            log.error('type error, seems received SIGTERM, err:{0}'.format(
                error)
            )
            msg = None
        except Exception as error:
            msg = 'Catch a error that I cannot handle, err_msg:%s' % error
            log.error(msg)
            log.error(type(error))
            raise CConnectionManager.QueueError(msg)
        return msg

    def _handle_new_recv(self, context):
        self._thdpool.add_1job(self.read, context)
        # self.read(context)

    def _finish_read_callback(self, succ, result):
        context = result
        if context.is_detroying():
            # destroy the context and socket
            context.release_readlock()
            try:
                self.cleanup_error_context(context)
            except KeyError:
                pass
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
            log.debug('The context is being destroyed. return')
            return
        if not context.try_readlock():
            return

        try:
            self._do_read(context)
            self._finish_read_callback(True, context)
        except Exception as error:
            context.to_destroy()
            log.info('read error occur, error type:{0}, content:{1}'.format(
                type(error), error)
            )
            self.cleanup_error_context(context)
            log.warn(traceback.format_exc())
            self._finish_read_callback(False, context)

    def _do_read(self, context):
        sock = context.get_sock()
        data = None
        context.move2recving_msg()
        while self._stopsign is not True:
            try:
                data = sock.recv(self.NET_RW_SIZE)
            except socket.error as error:
                err = error.args[0]
                if err == errno.EAGAIN:
                    log.debug(
                        'EAGAIN happend, peer info %s' %
                        context.get_context_info()
                    )
                    return context
                elif err == errno.EWOULDBLOCK:
                    log.info(
                        'EWOULDBLOCK happend, context info %s' %
                        context.get_context_info()
                    )
                    return context
                else:
                    log.debug(
                        'Socket error happend, error:%s,  peer info %s' %
                        (str(error), context.get_context_info())
                    )
                    context.to_destroy()
                    return context
            except Exception as error:
                log.critical(
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
            del data

    def _finish_write_callback(self, succ, result):
        """finish write callback"""
        context = result
        # You cannot do things below as getpeername will block if the conn
        # has problem!!!!!   - Guannan
        # try:
        #     context.get_sock().getpeername()
        # except socket.error as error:
        #   log.debug('Seems socket failed to getpeername:%s' % str(error))
        #   context.to_destroy()
        if context is not None and context.is_detroying():
            # destroy the context and socket
            context.release_writelock()
            try:
                self.cleanup_error_context(context)
            # pylint: disable=W0703
            except Exception as error:
                log.warn('context destroying encounters error,'
                    'skip it:{0}'.format(error)
                )
        else:
            # log.debug('to epoll modify')
            epoll_write_params = self._epoll_write_params()
            context.release_writelock()

    # context hash locked the writing.
    # guarantee there's only 1 thread for context writing.
    def _handle_new_send(self, context):
        """
        handle new send message
        """
        if context is None:
            log.debug('conetext is none')
            return
        self._thdpool.add_1job(self.add_write_job, context)

    def _do_write(self, context):
        """write into interface sending buffer"""
        sock = context.get_sock()
        msg = context.try_move2next_sending_msg()
        if msg is None:
            log.debug('send queue is empty, quit the _do_write thread')
            return context
        # log.debug('To enter write loop until eagin')
        # pylint:disable=w0212
        while not self._stopsign:
            data = msg.get_write_bytes(self.NET_RW_SIZE)
            log.debug('msg get_write_bytes_len to be sent: %d' % len(data))
            try:

                succ_len = sock.send(data)
                msg.seek_write(succ_len)
            except cuperr.AsyncMsgError as error:
                log.debug('has seek out of msg len, continue')
            except socket.error as error:
                err = error.args[0]
                if err == errno.EAGAIN:
                    log.debug(
                        'EAGAIN happend, context info %s' %
                        context.get_context_info()
                    )
                    return context
                elif err == errno.EWOULDBLOCK:
                    log.debug(
                        'EWOULDBLOCK happend, context info %s' %
                        context.get_context_info()
                    )
                    return context
                else:
                    log.warn(
                        'Socket error happend. But its not eagin,error:%s,\
                        context info %s, errno:%s' %
                        (str(error), context.get_context_info(), err)
                    )
                    context.to_destroy()
                    break
            except Exception as error:
                log.error(
                    'Socket error happend, error:%s,  context info %s, trace:%s' %
                    (str(error), context.get_context_info(), traceback.format_exc())
                )
                context.to_destroy()
                break
            finally:
                del data
            if msg.is_msg_already_sent():
                log.info(
                    'sent out a msg uniqid:{0}'.format(
                        async_msg.netmsg_tostring(msg))
                )
                # if we have successfully send out a msg. Then move to next one
                msg = context.try_move2next_sending_msg()
                if msg is None:
                    break
        return context

    def add_write_job(self, context):
        """
        add network write into queue
        """
        if context is None:
            return
        try:
            peerinfo = context.get_peerinfo()
        # pylint: disable=W0703
        except Exception as error:
            log.info('failed to get peerinfo, return')
            return
        if not context.try_writelock():
            log.debug(
                'Another thread is writing the context, return. '
                'Peerinfo:%s:%s' %
                (peerinfo[0], peerinfo[1])
            )
            return
        if context.is_detroying():
            log.info(
                'The context is being destroyed, i will do nothing. '
                'Peerinfo:%s:%s' %
                (peerinfo[0], peerinfo[1])
            )
            return
        try:
            # log.debug('write in add_write_job')
            self._do_write(context)
            self._finish_write_callback(True, context)
        # pylint: disable=W0703
        except Exception as error:
            log.debug(
                'seems error happend for context:%s Peerinfo:%s:%s\n, %s' %
                (str(error), peerinfo[0], peerinfo[1], traceback.format_exc())
            )
            self._finish_write_callback(False, context)

    def _get_resend_msg_key(self, ip, port, uniq_id):
        """generate resend msg key"""
        key = '{0}_{1}_{2}'.format(ip, port, uniq_id)
        return key

    def _check_needack_queue(self):
        """
        check needack_queue
        """
        log.debug('start check needack_queue')
        msg_item = None
        ack_flag = async_msg.MSG_FLAG2NUM['FLAG_ACK']
        while True:
            msg_item = None
            try:
                msg_item = self._needack_context_queue.get_nowait()
            except queue.Empty:
                log.debug('no need ack msg found yet')
                break
            ack_success = False
            toaddr = None
            uniq_id = msg_item.get_uniq_id()
            toaddr = msg_item.get_to_addr()[0]
            if msg_item.get_flag() & ack_flag == ack_flag:
                # if msg_item is a ack msg
                log.info(
                    'msgack received, stop resending '
                    'msguniq_id:{0}'.format(uniq_id)
                )
                msg_item.set_resend_flag(async_msg.MSG_RESEND_SUCCESS)
                toaddr = msg_item.get_from_addr()[0]
                ack_success = True
            to_ip = toaddr[0]
            to_port = toaddr[1]
            msg_key = self._get_resend_msg_key(to_ip, to_port, uniq_id)
            if ack_success:
                if msg_key in self._needack_context_dict:
                    last_msg = self._needack_context_dict[msg_key]
                    del self._needack_context_dict[msg_key]
                    self._executor.queue_exec(
                        last_msg.get_callback_function(),
                        executor.URGENCY_HIGH,
                        last_msg, True
                    )
                else:
                    log.warn(
                        'got duplicate ack-msg, msg_id:{0}'.format(uniq_id)
                    )
                continue
            # not ack_success + not in  context_dict
            else:
                if msg_key not in self._needack_context_dict:
                    self._needack_context_dict[msg_key] = msg_item
        time_out_list = []
        for key in self._needack_context_dict.keys():
            msg_item = self._needack_context_dict[key]
            msg_flag = msg_item.get_resend_flag()
            msg_info = 'msg_type:%d, msg_flag:%d, msg_dest:%s,uniqid:%d' % (
                msg_item.get_msg_type(),
                msg_item.get_flag(),
                str(msg_item.get_to_addr()),
                msg_item.get_uniq_id()
            )
            if msg_flag == async_msg.MSG_RESEND_SUCCESS:
                time_out_list.append(key)
                log.debug(
                    'del succ-msg from resending queue: {0}'.format(msg_info)
                )
            elif msg_flag == async_msg.MSG_RESENDING_FLAG:
                msg_total_timeout = msg_item.get_total_timeout()
                # if msg resending timeouts
                if msg_total_timeout <= 0:
                    msg_item.set_resend_flag(async_msg.MSG_TIMEOUT_TO_DELETE)
                    log.error(
                        'timeout, failed to get ack for netmsg:{0}'.format(
                            msg_info)
                    )
                    time_out_list.append(key)
                else:
                    msg_last_retry_time = msg_item.get_last_retry_time()
                    msg_retry_interval = msg_item.get_retry_interval()
                    now = time.time()
                    elapse_time = now - msg_last_retry_time
                    if elapse_time >= msg_retry_interval:
                        # update total_timeout
                        msg_item.set_total_timeout(
                            msg_total_timeout - elapse_time
                        )
                        msg_item.set_last_retry_time(now)
                        log.info('to resend CNeedAckMsg: {0}'.format(msg_info))
                        msg_item.pre_resend()
                        msg_item.add_retry_times()
                        self.push_msg2sendqueue(msg_item)
        for key in time_out_list:
            msg_item = self._needack_context_dict[key]
            del self._needack_context_dict[key]
            self._executor.queue_exec(
                msg_item.get_callback_function(),
                executor.URGENCY_NORMAL,
                msg_item, False
            )

    def do_check_msg_ack_loop(self):
        """
        check msg ack loop
        """
        log.debug('start check msg ack info.')
        self._check_needack_queue()
        self._executor.delay_exec(
            3,   # todo set the check_time to ?
            self.do_check_msg_ack_loop,
            urgency=executor.URGENCY_HIGH
        )

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
