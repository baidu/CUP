#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
"""
:description:
    network related module
"""
from __future__ import print_function
import os
import sys
import time
import socket
import struct
import warnings
try:
    import fcntl
except ImportError as error:
    # 'Seems run on non-linux machine'
    pass

from cup import log
from cup import platforms


__all__ = [
    'get_local_hostname',
    'get_hostip',
    'getip_byinterface',
    'set_sock_keepalive_linux',
    'set_sock_reusable',
    'set_sock_linger',
    'set_sock_quickack',
    'localport_free',
    'port_listened',
    'get_interfaces'
]


if platforms.is_linux():
    _SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _SOCKFD = _SOCK.fileno()
    _SIOCGIFADDR = 0x8915


def getip_byinterface(iface='eth0'):
    """
    get ipaddr of a network adapter

    :platform:
        Linux/Unix

    E.g.
    ::
        import cup
        print(cup.net.getip_byinterface('eth0'))
        print(cup.net.getip_byinterface('eth1'))
        print(cup.net.getip_byinterface('xgbe0'))
    """
    if platforms.is_linux():
        ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00' * 14)
        try:
            res = fcntl.ioctl(_SOCKFD, _SIOCGIFADDR, ifreq)
        except Exception as error:  # pylint: disable=W0703,W0612
            return None
        ipaddr = struct.unpack('16sH2x4s8x', res)[2]
        return socket.inet_ntoa(ipaddr)
    else:
        raise NotImplementedError('Not implemented on this platform')


def get_local_hostname():
    """
    get hostname of this machine
    """
    return str(socket.gethostname())


def get_hostip(hostname=None):
    """
    get ipaddr of a host

    :param hostname:
        None, by default, will use udp to get ipaddr for ipv4
        if not None, will use hostname to convert to ipaddr
    """
    ipaddr = None
    times = 0
    if hostname is not None:
        times = 0
        while times < 10:
            try:
                ipaddr = str(socket.gethostbyname(hostname))
                break
            except socket.gaierror:
                times += 1
                time.sleep(0.1)
        else:
            log.error('failed to get hostip for {0}'.format(hostname))
        return ipaddr
    else:
        while times < 10:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.connect(('8.8.8.8', 80))
                ipaddr = sock.getsockname()[0]
                break
            except socket.error:
                hostname = get_local_hostname()
                ipaddr = str(socket.gethostbyname(hostname))
                break
            finally:
                sock.close()
                times += 1
        else:
            log.error('failed to get hostip')
        return ipaddr


def set_sock_keepalive_linux(
        sock, after_idle_sec=1, interval_sec=3, max_fails=5
):
    """
    Set TCP keepalive on an open socket.
    It activates after 1 second (after_idle_sec) of idleness,
    then sends a keepalive ping once every 3 seconds (interval_sec),
    and closes the connection after 5 failed ping (max_fails), or 15 seconds

    :param sock:
        socket
    :param after_idle_sec:
        for TCP_KEEPIDLE. May not work, depends on ur system
    :param interval_sec:
        for TCP_KEEPINTVL
    :param max_fails:
        for TCP_KEEPCNT
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    except AttributeError:
        pass
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)


# pylint: disable=W0613
def set_keepalive_osx(sock, after_idle_sec=1, interval_sec=3, max_fails=5):
    """
    Set TCP keepalive on an open socket.
    Sends a keepalive ping once every 3 seconds (interval_sec)
    """
    # scraped from /usr/include, not exported by python's socket module
    # pylint: disable=C0103
    TCP_KEEPALIVE = 0x10
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPALIVE, interval_sec)


def set_sock_reusable(sock, resuable=True):
    """
    set socket reusable
    """
    value = 0
    if resuable:
        value = 1
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, value)


def set_sock_linger(sock, l_onoff=1, l_linger=0):
    """
    set socket linger param (socket.SO_LINGER)

    I.g.
    ::
        sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_LINGER,
            struct.pack('ii', 0, 0)
        )
    """
    # l_onoff = 1
    # l_linger = 0
    sock.setsockopt(
        socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(
            'ii', l_onoff, l_linger
        )
    )


def set_sock_quickack(sock):
    """
    open quickack for the socket

    I.g.
    ::
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
    """
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
    except AttributeError:
        pass


def localport_free(port, is_ipv6=False):
    """judge if a port is used. IPV4, by default"""
    return not port_listened(get_local_hostname(), port, is_ipv6)


def port_listened(host, port, is_ipv6=False):
    """check if the port is being listened on the host"""
    if is_ipv6:
        raise NotImplementedError('ipv6 not supported yet')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    set_sock_reusable(sock)
    listened = False
    try:
        result = sock.connect_ex((host, port))
        # 35 means EAGIN
        if result == 0 or result == 35:
            listened = True
    # pylint: disable=W0703
    except Exception as err:
        sys.stderr.write(err)
        sys.stderr.flush()
    finally:
        sock.close()
    return listened


def get_interfaces():
    """
    :return:
        a python list of network interfaces/adapters
    """
    eths = []
    srcpath = '/sys/class/net/'
    if os.path.exists(srcpath):
        interfaces = os.listdir(srcpath)
        for inter in interfaces:
            if inter == 'lo':
                continue
            eths.append(inter)
        return eths
    else:
        raise NotImplementedError('not supported other than linux')

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
