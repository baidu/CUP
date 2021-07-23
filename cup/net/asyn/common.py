#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
common function module for cup.net.asyn
"""
import socket
import struct

from cup import log
from cup.util import misc
from cup import platforms


__all__ = [
    'ip_port2connaddr', 'add_stub2connaddr', 'add_future2connaddr',
    'get_ip_and_port_connaddr', 'getip_connaddr', 'getport_connaddr',
    'getstub_connaddr', 'getfuture_connaddr'
]


PY3 = platforms.is_py3()
PY2 = platforms.is_py2()


def ip_port2connaddr(peer):
    """
    connaddr is a 128bit  int
        (32 -  32      32      32)
        ip - port   - stub - future

    :param peer:
        (ipaddr, port)
    :return:
        return a connaddr
    """
    misc.check_type(peer, tuple)
    ipaddr, port = peer
    # misc.check_type(ipaddr, str)
    packed = socket.inet_aton(ipaddr)
    return (struct.unpack("!L", packed)[0] << 96) | (port << 64)


def add_stub2connaddr(pack, stub):
    """
    add stub into connaddr
    """
    return pack | (stub << 32)


def add_future2connaddr(pack, future):
    """
    add future into connaddr
    """
    return pack | future


def get_ip_and_port_connaddr(pack):
    """
    get (ip, port) from connaddr
    """
    ipaddr = getip_connaddr(pack)
    port = getport_connaddr(pack)
    return (ipaddr, port)


def getip_connaddr(pack):
    """
    get ip from connaddr
    """
    return socket.inet_ntoa(struct.pack('!L', pack >> 96))


def getport_connaddr(pack):
    """
    get port from connaddr
    """
    return (pack >> 64) & 0x0000ffff


def getstub_connaddr(pack):
    """
    get stub from connaddr
    """
    return (pack >> 32) & 0x00000000ffff


def getfuture_connaddr(pack):
    """
    get future from conaddr
    """
    return pack & 0x000000000000ffff

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
