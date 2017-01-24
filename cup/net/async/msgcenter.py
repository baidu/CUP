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
:last_date:
    2014
:descrition:
    msg center related module
"""

import time
import socket
import threading
import abc

import cup
from cup.net.async import conn
from cup.net.async import msg as async_msg


__all__ = ['IMessageCenter']

# CHECK_OFF=0
# CHECK_ON=1

# pylint: disable=R0921
class IMessageCenter(object):
    """
    Message center class
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, ip, port, thdpool_param=None, stat_intvl=20):
        # super(self.__class__, self).__init__()
        if thdpool_param is None:
            thdpool_param = (3, 5)
        self._conn_mgr = conn.CConnectionManager(
            ip, port, thdpool_param
        )
        # self._check_flag = check_flag
        self._stop = False
        self._stat_intvl = stat_intvl
        self._stat_cond = threading.Condition()
        self._type_man = async_msg.CMsgType()
        self._type_man.register_types(async_msg.MSG_TYPE2NUM)

    def _bind_port(self):
        self._conn_mgr.bind()

    def setup(self):
        """
        setup the message center
        """
        try:
            self._bind_port()
            return True
        except socket.error as error:
            cup.log.error('bind error:{0}'.format(error))
            return False

    def dump_stat(self):
        """
        dump message center class
        """
        cup.log.info('dump_stat service started')
        while not self._stop:
            time.sleep(30)
            self._stat_cond.acquire()
            self._conn_mgr.dump_stats()
            self._stat_cond.wait(self._stat_intvl)
            self._stat_cond.release()
        cup.log.info('dump_stat service stopped')

    def post_msg(self, msg):
        """
        post a net msg
        """
        self._conn_mgr.push_msg2sendqueue(msg)

    def _post_ackok_msg(self, to_addr, from_addr, uniq_id):
        """
        create an ack msg
        """
        cup.log.info('post ack ok msg.')
        msg = async_msg.CNetMsg(is_postmsg=True)
        msg.set_to_addr(to_addr[0], to_addr[1])
        msg.set_from_addr(from_addr[0], from_addr[1])
        msg.set_msg_type(self._type_man.getnumber_bytype('ACK_OK'))
        msg.set_flag(1)
        msg.set_uniq_id(uniq_id)
        msg.set_body('')
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
        cup.log.info('handle in msgcenter')

    def default_handle(self, msg):  # pylint: disable=W0613,R0201
        """
        default handle for msgcenter
        """
        cup.log.warn('Get a msg that other cannot handle. Will skip it')
        del msg

    def _run_conn_manager(self):
        cup.log.info('run conn manager poll')
        self._conn_mgr.poll()

    # def _run_conn_msg_check_loop(self):
    #     cup.log.info('run conn manager check msg')
    #     # self._conn_mgr.run_executor()
    #     # self._conn_mgr.do_check_msg_ack_loop()

    def is_stopping(self):
        """
        is msg center being stopped
        """
        return self._stop

    def stop(self):
        """
        stop the message center
        """
        cup.log.info('To stop the msgcenter')
        self._conn_mgr.stop()
        self._stop = True
        self._stat_cond.acquire()
        self._stat_cond.notify()
        self._stat_cond.release()
        cup.log.info('msgcenter stopped')

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
        # if self._check_flag == CHECK_ON:
        #     cup.log.info('start run check msg transfer thread.')
        #     self._run_conn_msg_check_loop()
        ind = 0
        msg_ackflag = async_msg.MSG_FLAG2NUM['FLAG_ACK']
        while not self._stop:
            msg = self._conn_mgr.get_recv_msg()
            if ind >= 10000:
                recv_queue = self._conn_mgr.get_recv_queue()
                cup.log.info('recv queue size:{0}'.format(recv_queue.qsize()))
                ind = 0
            if msg is not None:
                # msg_addr = msg.get_to_addr()[0]
                # msg_ip = msg_addr[0]
                # msg_port = msg_addr[1]
                # uniq_id = msg.get_uniq_id()
                # msg_key = str(msg_ip) + '_' + str(msg_port) + '_' + str(uniq_id)
                # cup.log.info('msg[{0}] is already sent'.format(msg_key))
                # if msg.get_msg_type() == self._type_man.getnumber_bytype('HEART_BEAT') or \
                #         msg.get_msg_type() == self._type_man.getnumber_bytype('ACK_HEART_BEAT'):
                #     cup.log.info('get heart_beat msg')
                # elif msg.get_msg_type() == self._type_man.getnumber_bytype('ACK_OK'):
                #     cup.log.info('recv ack ok msg')
                #     self._conn_mgr.push_msg2needack_queue(msg)
                # elif msg.get_msg_type() == self._type_man.getnumber_bytype('NEED_ACK'):
                #     msg_to_addr = msg.get_to_addr()
                #     msg_from_addr = msg.get_from_addr()
                #     msg_uniq_id = msg.get_uniq_id()
                #     self._post_ackok_msg(msg_from_addr, msg_to_addr, msg_uniq_id)
                #     cup.log.info('handle msg in msgcenter run')
                #     self.handle(msg)
                ind += 1
                if msg_ackflag & msg.get_flag() == msg_ackflag:
                    self._conn_mgr.push_msg2needack_queue(msg)
                else:
                    self.handle(msg)
            msg = None
        return True

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
