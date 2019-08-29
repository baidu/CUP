#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
class CGeneratorMan(object)
===========================
Generate unique integers, strings and auto incremental uint.
Notice CGeneratorMan is a singleton class, which means cup will keep
only 1 instance per process.

:init:
    __init__(self, str_prefix=get_local_hostname())
        local hostname will be used by default.

:methods:
    **get_uniqname()**
        get unique name.
        Host-Level unique name (build upon str_prefix, pid, threadid)
    **get_next_uniq_num()**
        Process-level auto incremental uint. Thread-safe
    **reset_uniqid_start(num=0)**
        Reset next uniqid to which genman starts from
    **get_random_str()**
        Get random string by length
    **get_uuid()**
        Get uuid

"""
import os
import time
import random
import string
import socket
import struct
import threading

import cup
from cup import decorators


__all__ = [
    'CGeneratorMan',
    'CycleIDGenerator'
]


@decorators.Singleton
class CGeneratorMan(object):
    """
    refer to the docstring
    """
    def __init__(self, str_prefix='localhost'):

        """
        Generate unique integers, strings and auto incremental uint.
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
        get a unique name
        """
        self._lock.acquire()
        strrev = self._prefix + str(self._ind) + '_thd_' + \
            str(threading.current_thread().ident)
        self._ind = self._ind + 1
        self._lock.release()
        return strrev

    def get_next_uniq_num(self):
        """
        get next uniq num. Thread-safe
        """
        self._nlock.acquire()
        temp = self._nind
        self._nind += 1
        self._nlock.release()
        return temp

    def get_next_uniqhex(self):
        """
        return next uniqhex
        """
        temp = self.get_next_uniq_num()
        return str(hex(temp))

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
    cycle id generator. 128bit ID will be produced.
    128 bit contains:
        a. 64bit [ip, port, etc]  b. 64bit[auto increment id]
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
        self._next_id = int(time.time())

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
