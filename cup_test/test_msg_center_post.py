#!/bin/env python
# -*- coding: utf-8 -*
"""
    @author
    @brief
    @note
"""

import time
import random
import cup
import logging
import threading

import test_msg_center


@cup.decorators.Singleton
class MsgGenerator(object):
    def __init__(self, is_ack=False):
        self._flagman = cup.net.async.CMsgFlag()
        self._flagman.register_flags({
            'URGENT': 0,
            'NORMAL': 1,
        })
        self._type_man = cup.net.async.CMsgType()
        self._is_ack = is_ack

    def get_msg(self, self_ipport, to_ipport, i):
        msg = cup.net.async.CNetMsg(is_postmsg=True)
        msg.set_flag(self._flagman.getnumber_byflag('NORMAL'))
        msg.set_from_addr(self_ipport, (1, 2))
        msg.set_to_addr(to_ipport, (3, 4))
        msg.set_msg_type(self._type_man.getnumber_bytype('ACK'))
        msg.set_uniq_id(i)
        if self._is_ack:
            msg.set_body('ack')
        else:
            msg.set_body(128 * 1024 * 't')
        return msg


class CDifiPostCenter(cup.net.async.IMessageCenter):
    def __init__(self, ip, port):
        super(self.__class__, self).__init__(ip, port)
        self._type_man = cup.net.async.CMsgType()
        type2number = {
            'ACK': 1,
            'EXE': 2
        }
        self._type_man.register_types(type2number)
        self._msgman = MsgGenerator()
        self._self_ipport = (ip, port)
        self._to_ipport = (test_msg_center.SELF_IP, port - 2)

    def handle(self, msg):
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
        elif msg_type == self._type_man.getnumber_bytype('KILL'):
            print 'KILL'
        else:
            self.default_handle(msg)

    def post_a_msg(self):
        for i in xrange(0, 20000):
            msg = self._msgman.get_msg(self._self_ipport, self._to_ipport, i)
            self.post_msg(msg)

#    def run(self):
#        thd = threading.Thread(
#             target=super(self.__class__, self).run, args=()
#        )
#        thd.start()
#        self.post_a_msg()
#        time.sleep(300)
#        self.stop()

if __name__ == '__main__':
    self_ipport = ('10.226.71.38', test_msg_center.PORT_RECV + 2)
    cup.log.init_comlog(
        'recv_center', logging.DEBUG, './test.post.log',
        cup.log.ROTATION, 1024 * 1024 * 500, False
    )
    difi = CDifiPostCenter(self_ipport[0], self_ipport[1])
<<<<<<< HEAD
    difi.setup()
=======
    # difi.setup()
>>>>>>> origin/master
    thd = threading.Thread(target=difi.run)
    thd.start()
    difi.post_a_msg()
    time.sleep(4000)
    difi.stop()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
