#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:descrition:
    msg center related module
"""

import abc
import time
import socket
import threading

from cup import log
from cup.net.asyn import conn
from cup.net.asyn import msg as async_msg


__all__ = ['IMessageCenter']

# CHECK_OFF=0
# CHECK_ON=1


class IMessageCenter(object):
    """
    Message center class
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, ip, port, thdpool_param=None, stat_intvl=20):
        if thdpool_param is None:
            thdpool_param = (3, 5)
        self._conn_mgr = conn.CConnectionManager(
            ip, port, thdpool_param
        )
        self._stop = False
        self._stat_intvl = stat_intvl
        self._stat_cond = threading.Condition()
        self._type_man = async_msg.CMsgType()
        self._type_man.register_types(async_msg.MSG_TYPE2NUM)

    def _bind_port(self):
        """bind port for message center"""
        self._conn_mgr.bind()

    def global_sock_keepalive(self,
        after_idle_sec=1, interval_sec=3, max_fails=5
    ):
        """
        Set TCP keepalive on an open socket.
        It activates after 1 second (after_idle_sec) of idleness,
        then sends a keepalive ping once every 3 seconds (interval_sec),
        and closes the connection after 5 failed ping (max_fails), or 15 sec

        Notice, this will set all sockets this way.

        :param sock:
            socket
        :param after_idle_sec:
            for TCP_KEEPIDLE. May not work, depends on ur system
        :param interval_sec:
            for TCP_KEEPINTVL
        :param max_fails:
            for TCP_KEEPCNT
        """
        self._conn_mgr.global_sock_keepalive(
            after_idle_sec, interval_sec, max_fails
        )

    def setup(self):
        """
        setup the message center
        """
        try:
            self._bind_port()
            return True
        except socket.error as error:
            log.error('bind error:{0}'.format(error))
            return False

    def dump_stat(self):
        """
        dump message center class
        """
        log.info('mysql dump_stat service started')
        while not self._stop:
            ind = 0
            while ind < 30:
                ind += 1
                time.sleep(1)
                if self._stop:
                    log.info('msgcenter dump_stat service stopped')
                    return
            self._stat_cond.acquire()
            self._conn_mgr.dump_stats()
            self._stat_cond.wait(self._stat_intvl)
            self._stat_cond.release()
        log.info('msgcenter dump_stat service stopped')

    def post_msg(self, msg):
        """
        post a net msg
        """
        self._conn_mgr.push_msg2sendqueue(msg)

    def close_socket(self, msg, recv_socket=True):
        """close the socket by msg"""
        self._conn_mgr.close_socket(msg, recv_socket)

    def _post_ackok_msg(self, to_addr, from_addr, uniq_id):
        """
        create an ack msg
        """
        log.info('post ack ok msg.')
        msg = async_msg.CNetMsg(is_postmsg=True)
        msg.set_to_addr(to_addr[0], to_addr[1])
        msg.set_from_addr(from_addr[0], from_addr[1])
        msg.set_msg_type(self._type_man.getnumber_bytype('ACK_OK'))
        msg.set_flag(async_msg.MSG_FLAG2NUM['FLAG_NORMAL'])
        msg.set_uniq_id(uniq_id)
        msg.set_body('0')
        self.post_msg(msg)

    def pre_handle(self, msg, function):
        """pre_handle. Internal use ONLY. Do NOT call it directly."""
        function(msg)

    def _on_recv_ackmsg(self, netmsg):
        """on receiving ack msg"""

    @abc.abstractmethod
    def handle(self, msg):
        """
        handle function which should be implemented by
        sub-class.
        """
        log.info('handle in msgcenter')

    def default_handle(self, msg):  # pylint: disable=W0613,R0201
        """
        default handle for msgcenter
        """
        msg_ackflag = async_msg.MSG_FLAG2NUM['FLAG_ACK']
        if msg_ackflag & msg.get_flag() == msg_ackflag:
            # no need to handle it
            pass
        else:
            log.warn(
                'got a msg that you cannot hanlde, default will skip it. '
                'msg received, type:%d, flag:%d, from:%s, uniqid:%d' %
                (
                    msg.get_msg_type(),
                    msg.get_flag(),
                    str(msg.get_from_addr()),
                    msg.get_uniq_id()
                )
            )
            del msg

    def _run_conn_manager(self):
        """
        run conn manager
        """
        log.info('run conn manager poll')
        self._conn_mgr.poll()

    def is_stopping(self):
        """
        is msg center being stopped
        """
        return self._stop

    def stop(self, force_stop=False):
        """
        stop the message center
        """
        log.info('To stop the msgcenter')
        self._conn_mgr.stop(force_stop)
        self._stop = True
        self._stat_cond.acquire()
        self._stat_cond.notify()
        self._stat_cond.release()
        log.info('msgcenter stopped')

    def run(self):
        """
        run the msgcenter
        """
        if not self.setup():
            return False
        thd_conn_man = threading.Thread(target=self._run_conn_manager, args=())
        thd_conn_man.start()
        thd_stat = threading.Thread(target=self.dump_stat, args=())
        thd_stat.start()
        ind = 0
        msg_ackflag = async_msg.MSG_FLAG2NUM['FLAG_ACK']
        while not self._stop:
            msg = self._conn_mgr.get_recv_msg()
            if ind >= 10000:
                recv_queue = self._conn_mgr.get_recv_queue()
                log.info('msgcenter netmsg queue size:{0}'.format(
                    recv_queue.qsize()))
                ind = 0
            if msg is not None:
                try:
                    log.info(
                        'msg received, type:%d, flag:%d, from:%s, uniqid:%d' %
                        (
                            msg.get_msg_type(),
                            msg.get_flag(),
                            str(msg.get_from_addr()),
                            msg.get_uniq_id()
                        )
                    )
                    ind += 1
                    if msg_ackflag & msg.get_flag() == msg_ackflag:
                        self._conn_mgr.push_msg2needack_queue(msg)
                    self.handle(msg)
                # pylint: disable=W0703
                except Exception as err:
                    log.error(
                        'get a msg that cannot be handled.'
                        'Seems network err:{0}'.format(err)
                    )
            msg = None
        return True

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
