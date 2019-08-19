#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: YangGuang
"""
:description:
    host route info related module
"""
from __future__ import print_function
import copy
import json
import socket
import struct


__all__ = ['RouteInfo']


class RouteInfo(object):
    """
    Handler of Route Info for Linux system, for ipv4 only.

    *E.g.*
    ::

        from cup.net import route
        ri = route.RouteInfo()
        print(json.dumps(ri.get_route_by_ip('10.32.19.92'), indent=1))
        print(json.dumps(ri.get_routes(), indent=1))


    *Return*
    ::
        {
         "Use": "0",
         "Iface": "eth1",
         "Metric": "0",
         "Destination": "10.0.0.0",
         "Mask": "255.0.0.0",
         "RefCnt": "0",
         "MTU": "0",
         "Window": "0",
         "Gateway": "10.226.71.1",
         "Flags": "0003",
         "IRTT": "0"
        }
        [
         {
          "Use": "0",
          "Iface": "eth1",
          "Metric": "0",
          "Destination": "10.226.71.0",
          "Mask": "255.255.255.0",
          "RefCnt": "0",
          "MTU": "0",
          "Window": "0",
          "Gateway": "0.0.0.0",
          "Flags": "0001",
          "IRTT": "0"
         },
         {
          "Use": "0",
          "Iface": "eth1",
          "Metric": "0",
          "Destination": "169.254.0.0",
          "Mask": "255.255.0.0",
          "RefCnt": "0",
          "MTU": "0",
          "Window": "0",
          "Gateway": "0.0.0.0",
          "Flags": "0001",
          "IRTT": "0"
         },
         {
          "Use": "0",
          "Iface": "eth1",
          "Metric": "0",
          "Destination": "192.168.0.0",
          "Mask": "255.255.0.0",
          "RefCnt": "0",
          "MTU": "0",
          "Window": "0",
          "Gateway": "10.226.71.1",
          "Flags": "0003",
          "IRTT": "0"
         },
         {
          "Use": "0",
          "Iface": "eth1",
          "Metric": "0",
          "Destination": "172.16.0.0",
          "Mask": "255.240.0.0",
          "RefCnt": "0",
          "MTU": "0",
          "Window": "0",
          "Gateway": "10.226.71.1",
          "Flags": "0003",
          "IRTT": "0"
         },
         {
          "Use": "0",
          "Iface": "eth1",
          "Metric": "0",
          "Destination": "10.0.0.0",
          "Mask": "255.0.0.0",
          "RefCnt": "0",
          "MTU": "0",
          "Window": "0",
          "Gateway": "10.226.71.1",
          "Flags": "0003",
          "IRTT": "0"
         }
        ]

    """
    ROUTE_FILE = '/proc/net/route'

    def __init__(self):
        self._raw = []
        self._init_proc_info()

    @staticmethod
    def _ip2int(ip):
        """
        change ip address to integer
        :param ip: ip address in type of string
        :return: decimal integer in type of string
        """
        return struct.unpack("!I", socket.inet_aton(ip))[0]

    @staticmethod
    def _int2ip(dec):
        """
        change integer to ip address
        :param dec: decimal integer in type fo string
        :return: ip address
        """
        return socket.inet_ntoa(struct.pack("!I", dec))

    @staticmethod
    def _ip_check(ipaddr):
        q = ipaddr.split('.')
        ret = filter(
            lambda x: x >= 0 and x <= 255,
            map(int, filter(lambda x: x.isdigit(), q))
        )
        return (len(q) == 4) and (len(ret) == 4)

    def _init_proc_info(self):
        """
        read routeinfo from /proc/net/route, and parse it to dict
        this fun will be called when __init__
        """
        route_info = []
        with open(self.ROUTE_FILE, 'r') as fd:
            for line in fd.readlines():
                if line.startswith('Iface\t'):
                    continue
                d_item = {}
                items = line.split('\t')
                if len(items) != 11:
                    continue
                d_item['Iface'] = items[0]
                d_item['Destination'] = items[1]
                d_item['Gateway'] = items[2]
                d_item['Flags'] = items[3]
                d_item['RefCnt'] = items[4]
                d_item['Use'] = items[5]
                d_item['Metric'] = items[6]
                d_item['Mask'] = items[7]
                d_item['MTU'] = items[8]
                d_item['Window'] = items[9]
                d_item['IRTT'] = items[10].strip('\n').rstrip(' ')
                route_info.append(copy.deepcopy(d_item))

        self._raw = copy.deepcopy(route_info)

    def _raw2view(self, r):
        """
        change raw route_info to be readable
        :param r:
            raw route_info
        :return:
            readable route_info
        """
        res = copy.deepcopy(r)
        res['Destination'] = self._int2ip(
            socket.ntohl(int(r['Destination'], 16))
        )
        res['Gateway'] = self._int2ip(socket.ntohl(int(r['Gateway'], 16)))
        res['Mask'] = self._int2ip(socket.ntohl(int(r['Mask'], 16)))
        return res

    def get_routes(self):
        """
        get all the route_info of this host
        :return: all the readable route_info of this host
        """
        res_l = []
        for r in self._raw:
            res_l.append(self._raw2view(r))
        return res_l

    def get_interface_by_ip(self, ip):
        """
        get the interface which can reach to the ip
        :param ip:
            destination ip
        :return:
            interface name which can reach to the ip.
            None if failed.
        """
        if self._ip_check(ip) is False:
            return None
        route_info = self.get_route_by_ip(ip)
        if route_info is not None:
            return route_info['Iface']
        else:
            return None

    def get_route_by_ip(self, ip):
        """
        get the route_info which can reach to the ip address
        :param ip:
            destination ip address
        :return:
            route_info in type of dict
        """
        if self._ip_check(ip) is False:
            return None
        i_ip = socket.ntohl(int(self._ip2int(ip)))
        raw_route = self._raw
        ret = None
        for r in raw_route:
            if int(r['Destination'], 16) == i_ip & int(r['Mask'], 16):
                if ret is None:
                    ret = r
                    continue

                old = int(ret['Destination'], 16) & int(ret['Mask'], 16)
                new = int(r['Destination'], 16) & int(r['Mask'], 16)
                if old < new:
                    ret = r
                elif old == new:
                    if int(ret['Metric']) < int(r['Metric']):
                        ret = r
        return self._raw2view(ret)

    def get_interfaces(self):
        """get all the interface of this host"""
        itfs = set()
        for r in self._raw:
            itfs.add(r['Iface'])
        return list(itfs)


def _test():
    ri = RouteInfo()
    # print ri._ip2int('1.0.0.0')
    # print ri._raw_info
    # print
    # print json.dumps(ri.route, indent=1)
    print(json.dumps(ri.get_route_by_ip('10.32.19.92'), indent=1))
    print(json.dumps(ri.get_routes(), indent=1))
    # print(json.dumps(ri.get_routes(), indent=1))
    # print(ri.get_interfaces())
    # print('10.32.19.1:',ri._dot_decimal_to_hex('10.32.19.1'))
    # print('255.255.255.0:',ri._dot_decimal_to_hex('255.255.255.0'))
    # print('0113200A:',ri._hex_to_dot_decimal('0113200A'))
    # print(ri._get_net())
    # print(json.dumps(ri.route,indent=1))


if __name__ == '__main__':
    _test()
