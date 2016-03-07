#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################

"""
:author:
    Guannan Ma maguannan@baidu.com @mythmgn
:create_date:
    2014
:last_date:
    2014
:descrition:
    decorators related module
"""

from datetime import datetime as datetime_in
import platform
import time
import threading
from functools import wraps

import cup

__all__ = ['Singleton', 'needlinux', 'TraceUsedTime']


class Singleton(object):  # pylint: disable=R0903
    """
    Singleton你的类.
    用法如下::
        from cup import decorators

        @decorators.Singleton
        class YourClass(object):
            def __init__(self):
            pass
    """
    def __init__(self, cls):
        self.__instance = None
        self.__cls = cls
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        self._lock.acquire()
        if self.__instance is None:
            self.__instance = self.__cls(*args, **kwargs)
        self._lock.release()
        return self.__instance


def py_versioncheck(function, version):
    """
    :platform:
        any platform + any functions in python
    :param version:
        Version of python which should be <= version of the OS.
        *E.g. version=('2', '7', '0')*
        Python version should >= version.
    """
    ind = 0
    py_version = platform.python_version_tuple()
    for i in py_version:
        if int(version(ind)) < int(i):
            raise cup.err.DecoratorException(
                'Python version check failed. You expect version >= %s,'
                'but python-version on this machine:%s' %
                (version, py_version)
            )
        ind += 1
    return function


def needlinux(function):
    """
    只支持linux的python修饰符, 用来表明这个函数只能运行在linux系统上.
    如果函数运行在非linux平台, raise cup.err.DecoratorException

    :platform:
        Linux

    用法如下
    ::

        from cup import decorators
        @decorators.needlinux
        def your_func():
            pass
    """
    if platform.system() != 'Linux':
        raise cup.err.DecoratorException(
            'The system is not linux.'
            'This functionality only supported in linux'
        )
    return function


# pylint:disable=R0903
class TraceUsedTime(object):
    """
    追踪函数的耗时情况
    如果init过cup.log.init_comlog, 会打印到log文件。
    example::
        import time

        from cup import decorators

        @decorators.TraceUsedTime(True)
        def test():
            print 'test'
            time.sleep(4)


        # trace something with context. E.g. event_id
        def _test_trace_time_map(sleep_time):
            print "ready to work"
            time.sleep(sleep_time)


        traced_test_trace_time_map = decorators.TraceUsedTime(
            b_print_stdout=False,
            enter_msg='event_id: 0x12345',
            leave_msg='event_id: 0x12345'
        )(_test_trace_time_map)
        traced_test_trace_time_map(sleep_time=5)

    """
    def __init__(self, b_print_stdout=False, enter_msg='', leave_msg=''):
        """
        :param b_print_stdout:
            自动打印到由cup.log.init_comlog设置的logfile中，
            如果init_comlog未被调用和初始化，则不会打印。
            如果b_print_stdout=True, 则会同时打印时间追踪日志到stdout.

        :param enter_msg:
            会在函数进入时期也同步打印的msg

        :param leave_msg:
            会在函数离开时期同步打印的msg

        建议如果不使用cup.log.init_comlog打日志的话，则b_print_stdout=True
        """
        self._b_print_stdout = b_print_stdout
        self._enter_msg = enter_msg
        self._leave_msg = leave_msg

    def __call__(self, function):
        @wraps(function)
        def _wrapper_log(*args, **kwargs):
            now = time.time()
            if self._b_print_stdout:
                print '**enter func:%s,time:%s, msg:%s' % (
                    function, datetime_in.now(), self._enter_msg
                )
            cup.log.info(
                '**enter func:%s, msg:%s' % (function, self._enter_msg)
            )
            function(*args, **kwargs)
            then = time.time()
            used_time = then - now
            cup.log.info(
                '**leave func:%s, used_time:%f, msg:%s' % (
                    function, used_time, self._enter_msg
                )
            )
            if self._b_print_stdout:
                print '**leave func:%s, time:%s, used_time:%f, msg:%s' % (
                    function, datetime_in.now(), used_time, self._leave_msg
                )
        return _wrapper_log


# Things below for unittest
@TraceUsedTime(False)
def _test_trace_time():
    print 'now', time.time(), datetime_in.now()
    time.sleep(3)
    print 'then', time.time(), datetime_in.now()


@TraceUsedTime(True)
def _test_trace_time_log():
    print 'now', time.time(), datetime_in.now()
    time.sleep(3)
    print 'then', time.time(), datetime_in.now()


def _test_trace_time_map(sleep_time):
    print "ready to work"
    time.sleep(sleep_time)


def _test():
    cup.log.init_comlog(
        'test', cup.log.DEBUG, './test.log',
        cup.log.ROTATION, 102400000, False
    )
    _test_trace_time()
    _test_trace_time_log()
    func = TraceUsedTime(
        b_print_stdout=False,
        enter_msg='event_id: 0x12345',
        leave_msg='event_id: 0x12345'
    )(_test_trace_time_map)
    func(sleep_time=5)


if __name__ == '__main__':
    _test()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
