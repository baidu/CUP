#!/bin/env python
# -*- coding: utf-8 -*
"""
    @author
    @brief
    @note
"""

import cup
import logging

import test_msg_center_post

PORT_RECV = 61040
SELF_IP = '10.226.71.37'


class CDifiMsgCenter(cup.net.async.IMessageCenter):
    def __init__(self, ip, port):
        super(self.__class__, self).__init__(ip, port)
        self._type_man = cup.net.async.CMsgType()
        type2number = {
            'ACK': 1,
            'EXE': 2
        }
        self._type_man.register_types(type2number)
        self._msg_man = test_msg_center_post.MsgGenerator(True)
        self._count = 0

    def handle(self, msg):
        cup.log.debug('to handle msg in the child class')
        msg_type = msg.get_msg_type()
        if msg_type == self._type_man.getnumber_bytype('ACK'):
            cup.log.info(
                'get msg_type:ACK, msg_len:%d, msg_flag:%d, msg_src:%s, '
                'msg_dest:%s, uniqid:%d' %
                (
                    msg.get_msg_len(),
                    msg.get_flag(),
                    str(msg.get_from_addr()),
                    str(msg.get_to_addr()),
                    msg.get_uniq_id()
                )
            )
            src_peer, stub_future = msg.get_from_addr()
            reply_msg = self._msg_man.get_msg(
                (SELF_IP, PORT_RECV), src_peer, msg.get_uniq_id() + 10000
            )
            if self._count == 5:
                self.post_msg(reply_msg)
                self._count = 0
            else:
                self._count += 1
        elif msg_type == self._type_man.getnumber_bytype('KILL'):
            print 'KILL'
        else:
            self.default_handle(msg)

if __name__ == '__main__':
    cup.log.init_comlog(
        'recv_center', logging.INFO, './test.recv.log',
        cup.log.ROTATION, 1024 * 1024 * 500, False
    )
    difi = CDifiMsgCenter(SELF_IP, PORT_RECV)
    difi.setup()
    difi.run()
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
