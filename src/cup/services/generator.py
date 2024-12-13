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
    **get_random_str(length)**
        Get random string by length
    **get_uuid()**
        Get uuid

"""
import os
import sys
import time
import uuid
import random
import socket
import struct
import string
import hashlib
import warnings
import threading
try:
    # pylint: disable=reportMissingImports
    import Queue as queue
except ImportError:
    import queue

import cup
from cup import log
from cup import decorators
if sys.version_info[0] >= 3:
    unicode = str
    LOWERCASES = f'{string.ascii_lowercase}{string.digits}'
else:
    LOWERCASES = string.lowercase


__all__ = [
    'CGeneratorManBase',
    'Py3Generator',
    'CycleIDGenerator',
    'CachedUUID'
]


UUID1 = 0
UUID4 = 1
_UUID_LISTS_FUNCS = [
    uuid.uuid1,
    uuid.uuid4
]


class CGeneratorManBase(object):
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
        return ''.join(random.choice(LOWERCASES) for _ in range(length))

    @classmethod
    def get_uuid(cls):
        """get random uuid"""
        return uuid.uuid4().hex


@decorators.Singleton
class CGeneratorMan(CGeneratorManBase):
    """
    """
    def __init__(self, str_prefix='localhost'):
        super().__init__(str_prefix)
    

class Py3Generator(CGeneratorManBase):
    """py3 generator"""

    def __init__(self, str_prefix='localhost'):

        """
        Generate unique integers, strings and auto incremental uint.
        """
        super().__init__(str_prefix)

    @classmethod
    @decorators.Singleton
    def single_instance(cls, str_prefix='localhost'):
        """
        get single instance of this class
        """
        return Py3Generator(str_prefix)


class CycleIDGenerator(object):
    """
    cycle id generator. 128bit ID will be produced.

    128 bit contains: a. 64bit [ip, port, etc]  b. 64bit[auto increment id]
    """
    
    def __init__(self, ipaddr, port):
        """
        ip, port will be encoded into the ID
        """
        self._ip = ipaddr
        self._port = port
        self._lock = threading.Lock()
        packed = socket.inet_aton(self._ip)
        tmp = struct.unpack("!L", packed)[0] << 96
        self._pre_num = tmp | (int(self._port) << 80)
        self._max_id = 0X1 << 79
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
        str_num = hex(num)
        return str_num[2:]
    
    @classmethod
    def id2_hexstring_0x(cls, num):
        """return hex of the id"""
        str_num = hex(num)
        return '0x{0}'.format(str_num[2:])
    
    
    @classmethod
    def hex2id(cls, hexnum: str):
        """
        hex2id
        """
        return int(hexnum, 16)
    
    @classmethod
    def ipport(cls, hexnum):
        """
        :raise:
            ValueError if cannot convert it to ip port
        """
        try:
            id = cls.hex2id(hexnum)
            ip = socket.inet_ntoa(struct.pack('!L', id >> 96))
            port = id >> 80 & 0xffff
            return ip, port
        except struct.error as err:
            raise ValueError('failed to convert the hex')



class CachedUUID(object):
    """cached uuid object"""
    def __init__(self, mode=UUID1, max_cachenum=100):
        """
        ip, port will be encoded into the ID
        """
        if mode > len(_UUID_LISTS_FUNCS):
            raise ValueError('only support UUID1 UUID4')
        self._uuidgen = _UUID_LISTS_FUNCS[mode]
        self._fifoque = queue.Queue(max_cachenum)
        self._max_cachenum = max_cachenum
    
    def _thd_gen_uuid(self, num=50):
        self.gen_cached_uuid(num)

    def get_uuid(self, num=1):
        """
        get serveral uuids by 'num'

        :return:
            a list of uuids (in hex string)
        """
        ret = []
        while num > 0:
            try:
                item = self._fifoque.get(block=False)
                ret.append(item)
                num -= 1
            except queue.Empty:
                self.gen_cached_uuid(num=1)
                thd = threading.Thread(
                    target=self._thd_gen_uuid, name='gen uuid', daemon=True
                )
                thd.start()
        return ret

    def gen_cached_uuid(self, num=50):
        """
        generate num of uuid into cached queue
        """
        while num > 0:
            try:
                md5obj = hashlib.md5()
                hexstr = self._uuidgen().hex
                if isinstance(hexstr, unicode):
                    md5obj.update(hexstr.encode('utf-8'))
                else:
                    md5obj.update(hexstr)
                self._fifoque.put(md5obj.hexdigest(), block=False)
                num -= 1
            except queue.Full:
                break
        size = self._fifoque.qsize()
        log.info('after generate cached uuid queue size :{0}'.format(size))
    
    @classmethod
    @decorators.Singleton
    def singleton_instance(cls, mode=UUID1, max_cachenum=100, firstinit=False):
        return CachedUUID(mode, max_cachenum)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
