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

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
