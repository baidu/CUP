#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Author: Zhaominghao, Guannan Ma
"""
:description:
    cup thread module
"""

__all__ = ['async_raise', 'CupThread', 'RWLock', 'thread_alive']


import threading
import time
import ctypes

import cup


def async_raise(tid, exctype):
    """
    Raises an exception in the threads with id tid

    :param tid:
        thread id in python
    :param exctype:
        exception class, e.g. IOError

    """
    return ctypes.pythonapi.PyThreadState_SetAsyncExc(
        tid,
        ctypes.py_object(exctype)
    )


def thread_alive(obj):
    """
    check if thread is alive. Py2 py3 compatible

    :raise Exception:
        if the obejct does not have attr obj.is_alive and obj.isAlive,
        the lib will raise ValueError
    """
    if hasattr(obj, 'is_alive'):
        return obj.is_alive()
    elif hasattr(obj, 'isAlive'):
        return obj.isAlive()
    else:
        raise ValueError('obj is not a object instance of threading.Thread')


class CupThread(threading.Thread):
    """
    CupThread is a sub-class inherited from threading.Thread;

    .. HINT::

        CupThread has 3 more methods:

        1. raise_exc, to send a raise-exception signal to the thread,\
            TRY to let the thread raise an exception.
        2. get_my_tid, get thread id
        3. terminate, to stop the thread

    .. CAUTION::

        Notice if a thread is busy running under kernel-sysmode, it may not
        response to the signals! In other words, it may not raise any
        exception/terminate even though cup has send a CupThread signal!
    """

    def get_my_tid(self):
        """
        return thread id
        """
        if not thread_alive(self):
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
        return None

    def raise_exc(self, exctype):
        """
        asynchrously send 'raise exception' signal to the thread.

        :param exctype:
            raise Exception, exctype type is class
        :return:
            return 1 on success. 0 otherwise.
        """
        return async_raise(self.get_my_tid(), exctype)

    def terminate(self, times=15):
        """
        asynchrously terminate the thread.

        Return True if the termination is successful or the thread is already
        stopped. Return False, otherwise.

        :times:
            retry times until call for failure.
        """
        cnt = 0
        while thread_alive(self):
            self.raise_exc(cup.err.ThreadTermException)
            time.sleep(1)
            cnt += 1
            if cnt > times:
                return False
        return True


class RWLock(object):
    """
    Read Write Lock is a typical lock type in computer world.

    Code example:
    ::

        from cup import thread
        rwlock = thread.RWLock()
        # can acquire read lock
        rwlock.acquire_readlock()
        # can acquire read lock again if there has not been WRITE locked
        rwlock.acquire_readlock()   # <-- this will succeed
        # rwlock.acquire_writelock()  # <--- this will hang if uncommented
        rwlock.release_readlock()
        rwlock.acquire_writelock()
        # rwlock.acquire_readlock() # <--- this will hang if uncommented
        rwlock.release_writelock()

    """
    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._rd_num = 0
        self._wt_num = 0

    def acquire_writelock(self, wait_time=None):
        """
        Acquire write lock.

        .. IMPORTANT::

            If wait_time is not None and wait_time >=0,
            cup will wait until wait_time passes. If the call timeouts and
            cannot get the lock, will raise RuntimeError
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
        release write lock
        """
        self._cond.acquire()
        self._wt_num -= 1
        if self._wt_num == 0:
            self._cond.notify_all()
        self._cond.release()

    def acquire_readlock(self, wait_time=None):
        """
        Acquire readlock.

        :param wait_time:
            same to wait_time for acquire_writelock

        :raise:
            RuntimeError if after wait_time, cup still can NOT getthe lock
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
        release read lock
        """
        self._cond.acquire()
        self._rd_num -= 1
        if self._rd_num == 0 and self._wt_num == 0:
            self._cond.notify()
        self._cond.release()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
