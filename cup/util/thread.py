#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################
"""
:author:
    Zhaominghao Guannan Ma
:create_date:
    2014
:last_date:
    2014
:descrition:
    cup thread module
"""

__all__ = ['async_raise', 'CupThread', 'RWLock']


import threading
import time
import ctypes

import cup


def async_raise(tid, exctype):
    """Raises an exception in the threads with id tid"""
    return ctypes.pythonapi.PyThreadState_SetAsyncExc(
        tid,
        ctypes.py_object(exctype)
    )


class CupThread(threading.Thread):
    """
    CupThread继承threading.Thread, 支持threading.Thread所有功能和特性,
    CupThread扩展了三个功能,raise_exc给线程发送raise信号,get_my_tid返回线程id，
    terminate同步中止线程
    """
    def get_my_tid(self):
        """
        返回线程id
        """
        if not self.isAlive():
            cup.log.warn('the thread is not active')
            return None
        # do we have it cached?
        if hasattr(self, '_thread_id'):
            # pylint: disable=E0203
            return self._thread_id
        # pylint: disable=W0212
        # no, look for it in the _active dict
        for tid, tobj in threading._active.items():
            if tobj is self:
                # pylint: disable=W0201
                self._thread_id = tid
                return tid

    def raise_exc(self, exctype):
        """
        异步给线程发送raise，发送成功返回1，线程已经停止返回0，其他错误返回!=1
        :param exctype:
            raise Exception, exctype type is class
        """
        return async_raise(self.get_my_tid(), exctype)

    def terminate(self, times=15):
        """
        异步raise线程，尝试中止线程
        中止成功返回True，
        线程已经停止返回True，
        停止失败返回False。
        (在返回True的时候，表示线程已经被中止,
        在中止失败的过程中，会重试times次)
        """
        cnt = 0
        while self.isAlive():
            self.raise_exc(cup.err.ThreadTermException)
            time.sleep(1)
            cnt += 1
            if cnt > times:
                return False
        return True


class RWLock(object):
    """
    读写锁类
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._rd_num = 0
        self._wt_num = 0

    def acquire_writelock(self, wait_time=None):
        """
        获取写锁， 如果wait_time赋值且!=None的数，会等待wait_time.
        如果之后还没拿到锁， 将raise RuntimeError
        """
        self._cond.acquire()
        if self._wt_num > 0 or self._rd_num > 0:
            try:
                self._cond.wait(wait_time)
            except RuntimeError as error:
                raise RuntimeError(str(error))
        self._wt_num += 1
        self._cond.release()

    def release_writelock(self):
        """
        释放写锁
        """
        self._cond.acquire()
        self._wt_num -= 1
        if self._wt_num == 0:
            self._cond.notify_all()
        self._cond.release()

    def acquire_readlock(self, wait_time=None):
        """
        获取读锁， 如果wait_time赋值且!=None的数，会等待wait_time.
        如果之后还没拿到锁， 将raise RuntimeError
        """
        self._cond.acquire()
        if self._wt_num > 0:
            try:
                self._cond.wait(wait_time)
            except RuntimeError as error:
                raise RuntimeError(error)
        self._rd_num += 1
        self._cond.release()

    def release_readlock(self):
        """
        释放读锁
        """
        self._cond.acquire()
        self._rd_num -= 1
        if self._rd_num == 0 and self._wt_num == 0:
            self._cond.notify()
        self._cond.release()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
