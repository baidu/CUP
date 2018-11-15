#!/bin/env python
# -*- coding: utf-8 -*
"""
    Author: (Guannan Ma)
"""

import os
import sys
import socket

_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, _NOW_PATH + '../')

from cup import net
from cup import unittest


def test_port_free():
    """test port_listened"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((net.get_hostip(), 61113))
    sock.settimeout(1)
    net.set_sock_reusable(sock)
    sock.listen(1)
    ret = net.localport_free(61113)
    unittest.assert_eq(ret, False)
    unittest.assert_eq(
        net.port_listened(net.get_local_hostname(), 61113),
        True
    )
    sock.close()

test_port_free()
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
