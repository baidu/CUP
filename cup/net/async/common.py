#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
common function module for cup.net.async
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
    connaddr is a 64bit int
        32 -  16    - 16   - 32
        ip - port   - stub - future

    :param peer:
        (ipaddr, port)
    :return:
        return a connaddr
    """
    misc.check_type(peer, tuple)
    ipaddr, port = peer
    misc.check_type(ipaddr, str)
    packed = socket.inet_aton(ipaddr)
    return (struct.unpack("!L", packed)[0] << 64) | (port << 48)


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
    return socket.inet_ntoa(struct.pack('!L', pack >> 64))


def getport_connaddr(pack):
    """
    get port from connaddr
    """
    return (pack >> 48) & 0xffff


def getstub_connaddr(pack):
    """
    get stub from connaddr
    """
    return (pack >> 32) & 0xffff


def getfuture_connaddr(pack):
    """
    get future from conaddr
    """
    return (pack) & 0xffff

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
