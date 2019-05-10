#!/usr/bin/env python
# -*- coding: utf-8 -*
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    Connection Context for each socket
"""
import copy
import time
import threading
import traceback
try:
    import Queue as queue  # pylint: disable=F0401
except ImportError:
    import queue   # pylint: disable=F0401

import cup
from cup import log
from cup.util import misc
from cup.net.async import msg as async_msg


__all__ = [
    'CConnContext'
]



class CConnContext(object):  # pylint: disable=R0902
    """
    connection context for each socket
    """
    CONTEXT_QUEUE_SIZE = 200
    def __init__(self):
        self._destroying = False
        self._sock = None
        self._peerinfo = None

        self._sending_msg = None
        self._send_queue = queue.PriorityQueue(self.CONTEXT_QUEUE_SIZE)
        self._recving_msg = None
        self._recv_queue = queue.PriorityQueue(self.CONTEXT_QUEUE_SIZE)
        self._msgind_in_sendque = 0
        self._is_reading = None
        self._is_1st_recv_msg = True
        self._is_1st_send_msg = True
        self._conn = None
        self._lock = threading.Lock()
        self._readlock = threading.Lock()
        self._writelock = threading.Lock()

        self._retry_interval = None
        self._total_timeout = None
        self._last_retry_time = None
        self._function = None
        self._resend_flag = None
        self._listened_peer = None

    def to_destroy(self):
        """
        destroy context
        """
        self._lock.acquire()
        self._destroying = True
        if self._sock is None:
            msg = 'context is with no sock'
        else:
            msg = 'context with socket: {0}, peer:{1}'.format(
                    self._sock, self.get_peerinfo())
        log.debug('({0}) is to be destroyed'.format(msg))
        self._lock.release()

    def is_detroying(self):
        """
        is context being destroyed
        """
        self._lock.acquire()
        is_destryoing = self._destroying
        self._lock.release()
        return is_destryoing

    def set_destoryed(self):
        """set context to destroyed status"""
        self._lock.acquire()
        self._destroying = False
        self._lock.release()

    def set_conn_man(self, conn):
        """
        set conn for context
        """
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
        try:
            ret = self._recving_msg.push_data(data)
        except IndexError as error:
            log.warn('index error/msg len error happened:{0}'.format(error))
            log.warn(traceback.format_exc())
            log.warn('receive a msg that cannot handle, close the socket')
            self.to_destroy()
            return
        if ret < 0:
            log.warn(
                'receive an wrong socket msg, to close the peer:{0}'.format(
                    self.get_peerinfo()
                )
            )
            self.to_destroy()
            self._conn.cleanup_error_context(self)
            return
        if data_len >= ret:
            if self._recving_msg.is_recvmsg_complete():
                self._is_1st_recv_msg = False
                self._conn.get_recv_queue().put(
                    (self._recving_msg.get_flag(), self._recving_msg)
                )
                if self.get_listened_peer() is None:
                    listened_peer = self._recving_msg.get_from_addr()[0]
                    self.set_listened_peer(listened_peer)
                    log.info(
                        'set listened peer {0} for this context({1})'.format(
                            listened_peer, self._peerinfo)
                    )
                self._recving_msg = None
                if self._conn.get_recv_queue().qsize() >= 500:
                    time.sleep(0.1)
                self.move2recving_msg()
            #  the pushed data should span on two msg datas
            if data_len > ret:
                return self.do_recv_data(data[ret:], (data_len - ret))
        else:
            log.error(
                'Socket error. We cannot get more than pushed data length'
            )
            assert False
        return

    def move2recving_msg(self):
        """
        get the net msg being received
        """
        #  if no recving msg pending there, create one.
        if self._recving_msg is None:
            self._recving_msg = async_msg.CNetMsg(is_postmsg=False)
            self._recving_msg.set_msg_context(self)
        if self._is_1st_recv_msg:
            self._recving_msg.set_need_head(True)
        else:
            self._recving_msg.set_need_head(False)

    def try_move2next_sending_msg(self):
        """
        move to next msg that will be sent
        """
        if self._sending_msg is None or \
                self._sending_msg.is_msg_already_sent():
            try:
                item = self._send_queue.get_nowait()
                msg = item[2]
            except queue.Empty:
                # log.debug('The send queue is empty')
                msg = None
            except Exception as error:
                errmsg = (
                    'Catch a error that I cannot handle, err_msg:%s' %
                    str(error)
                )
                log.error(errmsg)
                raise ValueError(errmsg)
            self._sending_msg = msg
        else:
            log.debug(
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

        :param return:
            return 0 on success
            return 1 on TRY_AGAIN ---- queue is full. network is too busy.

        :TODO:
            If the msg queue is too big, consider close the network link
        """
        succ = None
        self._lock.acquire()
        if self._is_1st_send_msg:
            msg.set_need_head(True)
            # pylint: disable=W0212
            msg._set_msg_len()
            self._is_1st_send_msg = False
        else:
            msg.set_need_head(False)
            msg._set_msg_len()
        urgency = 1
        is_urgent = flag & async_msg.MSG_FLAG2NUM['FLAG_URGENT']
        if is_urgent == async_msg.MSG_FLAG2NUM['FLAG_URGENT']:
            urgency = 0
        try:
            self._send_queue.put_nowait((urgency, self._msgind_in_sendque, msg))
            self._msgind_in_sendque += 1
            succ = 0
        except queue.Full:
            log.debug(
                'network is busy. send_msg_queue is full, peerinfo:{0}'.format(
                    msg.get_to_addr()[0]
                )
            )
            succ = 1
        self._lock.release()
        return succ

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

    def get_listened_peer(self):
        """
        return peer listened peer info
        """
        return self._listened_peer

    def set_listened_peer(self, peer):
        """
        set peer listened peer
        """
        self._listened_peer = peer

    def get_sending_queue(self):
        """return sending queue"""
        return self._send_queue

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
