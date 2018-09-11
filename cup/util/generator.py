#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
class CGeneratorMan(object)
===========================
用来生成各类唯一数，字符集，线程安全的自增uint的类。
目前生成函数较少， 欢迎大家贡献ci.
Singleton类。初始化需要传入一个用来生成字符集的string.

:初始化函数:
    __init__(self, str_prefix=get_local_hostname())
        默认传入当前自己的hostname

:成员函数:
    **get_uniqname()**
        获得一个以传入的初始化string为base, 加上pid, threadid等组合的host级别的
        unique string.
    **get_next_uniq_num()**
        获得当前进程唯一的自增非负整数。线程安全.

"""
import os
import random
import string
import socket
import struct
import threading

import cup
from cup import decorators


@decorators.Singleton
class CGeneratorMan(object):
    """
    数据生成类，具体功能见函数说明

    """
    def __init__(self, str_prefix='localhost'):

        """
        CGeneratorMan是一个Singleton模式的类.
        这样能保证同一个进程中的数字、字符串等生成函数是一致的。
        """
        if str_prefix == 'localhost':
            prefix = cup.net.get_local_hostname()
        else:
            prefix = str(str_prefix)
        self._prefix = prefix + str(os.getpid())
        self._lock = threading.Lock()
        self._ind = 0
        self._nlock = threading.Lock()
        self._nind = 0

    def reset_uniqid_start(self, num=0):
        """
        reset next uniqid to which genman starts from.
        """
        self._lock.acquire()
        self._nind = num
        self._lock.release()

    def get_uniqname(self):
        """
        获得一个线程安全的unique字符串
        """
        self._lock.acquire()
        strrev = self._prefix + str(self._ind) + '_thd_' + \
            str(threading.current_thread().ident)
        self._ind = self._ind + 1
        self._lock.release()
        return strrev

    def get_next_uniq_num(self):
        """
        获得线程安全的下一个unique id.
        该id每获得一次增加1.
        """
        self._nlock.acquire()
        temp = self._nind
        self._nind += 1
        self._nlock.release()
        return temp

    @classmethod
    def get_random_str(cls, length):
        """get random str by length"""
        return ''.join(random.choice(string.lowercase) for i in range(length))

    @classmethod
    def get_uuid(cls):
        """get random uuid"""
        import uuid
        uuid.uuid4()


class CycleIDGenerator(object):
    """
    cycle id generator. 128bit

    64bit [ip, port, etc] 64bit[auto increment id]
    """
    def __init__(self, ip, port):
        """
        ip, port will be encoded into the ID
        """
        self._ip = ip
        self._port = port
        self._lock = threading.Lock()
        packed = socket.inet_aton(self._ip)
        tmp = struct.unpack("!L", packed)[0] << 96
        self._pre_num = tmp | (int(self._port) << 64)
        self._max_id = 0X1 << 63
        self._next_id = 0

    def reset_nextid(self, nextid):
        """reset nextid that will return to you"""
        self._lock.acquire()
        if nextid > self._max_id:
            self._lock.release()
            return False
        self._next_id = nextid
        self._lock.release()
        return True

    def next_id(self):
        """get next id"""
        self._lock.acquire()
        num = self._pre_num | self._next_id
        if self._next_id == self._max_id:
            self._next_id = 0
        else:
            self._next_id += 1
        self._lock.release()
        return num

    @classmethod
    def id2_hexstring(cls, num):
        """return hex of the id"""
        str_num = str(hex(num))
        return str_num


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
