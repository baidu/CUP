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
"""

import socket
import struct

from cup.util import misc


__all__ = [
    'ip_port2connaddr', 'add_stub2connaddr', 'add_future2connaddr',
    'get_ip_and_port_connaddr', 'getip_connaddr', 'getport_connaddr',
    'getstub_connaddr', 'getfuture_connaddr'
]


def ip_port2connaddr(peer):
    """
    connaddr是个64bit的int
        32 -  16    - 16   - 32
        ip - port   - stub - future
    该函数以peer(ipaddr, port)为输入参数， 生成一个connaddr
    """
    misc.check_type(peer, tuple)
    ipaddr, port = peer
    misc.check_type(ipaddr, str)
    packed = socket.inet_aton(ipaddr)
    return ((struct.unpack("!L", packed)[0] << 64) | (port << 48))


def add_stub2connaddr(pack, stub):
    """
    connaddr是个64bit的int
        32 -  16    - 16   - 32
        ip - port   - stub - future
    该函数设置connaddr中的stub到connaddr
    """
    return (pack | (stub << 32))


def add_future2connaddr(pack, future):
    """
    connaddr是个64bit的int
        32 -  16    - 16   - 32
        ip - port   - stub - future
    该函数设置connaddr中的future到connaddr
    """
    return (pack | future)


def get_ip_and_port_connaddr(pack):
    """
    connaddr是个64bit的int
        32 -  16    - 16   - 32
        ip - port   - stub - future
    该函数获取connaddr中的(ip, port)
    """
    ipaddr = getip_connaddr(pack)
    port = getport_connaddr(pack)
    return (ipaddr, port)


def getip_connaddr(pack):
    """
    connaddr是个64bit的int
        32 -  16    - 16   - 32
        ip - port   - stub - future
    该函数获取connaddr中的ip
    """
    return socket.inet_ntoa(struct.pack('!L', pack >> 64))


def getport_connaddr(pack):
    """
    connaddr是个64bit的int
        32 -  16    - 16   - 32
        ip - port   - stub - future
    该函数获取connaddr中的port
    """
    return ((pack >> 48) & 0xffff)


def getstub_connaddr(pack):
    """
    connaddr是个64bit的int
        32 -  16    - 16   - 32
        ip - port   - stub - future
    该函数获取connaddr中的stub
    """
    return ((pack >> 32) & 0xffff)


def getfuture_connaddr(pack):
    """
    connaddr是个64bit的int
        32 -  16    - 16   - 32
        ip - port   - stub - future
    该函数获取connaddr中的future
    """
    return ((pack) & 0xffff)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
