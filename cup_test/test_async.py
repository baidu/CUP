#!/bin/env python
# -*- coding: utf-8 -*
"""
    @author
    @brief
    @note
"""

import cup
from cup.unittest import CUTCase
from cup.unittest import CCaseExecutor
from cup.net.async import CNetMsg
from cup.net.async import ip_port2connaddr
from cup.net.async import add_stub2connaddr
from cup.net.async import add_future2connaddr


class CTestAsync(CUTCase):
    def __init__(self):
        super(self.__class__, self).__init__()

    def setup(self):
        pass

    def teardown(self):
        pass

    def _constrct_msg(self):
        msg = CNetMsg()
        msg.set_need_head(True)
        msg.push_data(msg.MSG_SIGN)
        cup.unittest.assert_eq(msg._data['head'], msg.MSG_SIGN)
        del msg

        msg = CNetMsg()
        msg.set_need_head(True)
        msg.push_data(msg.MSG_SIGN[0: len(msg.MSG_SIGN) - 2])
        msg.push_data(msg.MSG_SIGN[len(msg.MSG_SIGN) - 2: len(msg.MSG_SIGN)])
        msg.push_data(msg.asign_uint2byte_bybits(4578910, 64))
        cup.unittest.assert_eq(msg._data['head'], msg.MSG_SIGN)
        cup.unittest.assert_eq(
            msg.convert_bytes2uint(msg._data['msg_len']), 4578910
        )

        peer = ('137.2.23.44', 6300)
        pack = ip_port2connaddr(peer)
        pack = add_stub2connaddr(pack, 15500)
        pack = add_future2connaddr(pack, 45678)

        data = msg.asign_uint2byte_bybits(pack, 128)
        reverse_data = msg.convert_bytes2uint(data)

        cup.unittest.assert_eq(
            cup.net.async.get_ip_and_port_connaddr(reverse_data),
            ('137.2.23.44', 6300)
        )

        cup.unittest.assert_eq(
            cup.net.async.getstub_connaddr(reverse_data),
            15500
        )

        cup.unittest.assert_eq(
            cup.net.async.getfuture_connaddr(reverse_data),
            45678
        )

    def test_run(self):
        pass
        # self.test_msg()


if __name__ == '__main__':
    CCaseExecutor().runcase(CTestAsync())

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
