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
:descrition:
    misc functions
"""
import os
import sys


class CAck(object):
    """
    Ack, 可设置bool值并获取
    """
    def __init__(self, binit=False):
        self._rev = binit

    def getack_infobool(self):
        """
        取得ack的bool返回值
        """
        return self._rev

    def setack_infobool(self, binit=False):
        """
        设置ack的bool值
        """
        self._rev = binit


def check_type(param, expect):
    """
    检查param是否和expect一样的类型。如果不一样raise TypeError
    """
    if type(param) != expect:
        raise TypeError('TypeError. Expect:%s, got %s' % (expect, type(param)))


def check_not_none(param):
    """
    检查param不是None, 如果是None, raise NameError
    """
    if param is None:
        raise NameError('The param has not been set before access')


def get_funcname(backstep=0):
    """
    获得调用该函数的代码行所在的函数名。 backstep代表是否将调用栈增/减.
    backstep默认0
    """
    # pylint: disable=W0212
    return sys._getframe(
        backstep + 1).f_code.co_name


def get_filename(backstep=0):
    """
    获得调用该函数的代码行所在的文件名。 backstep代表是否将调用栈增/减.
    """
    return os.path.basename(
        sys._getframe(backstep + 1).f_code.co_filename)  # pylint:disable=W0212


def get_lineno(backstep=0):
    """
    获得调用该函数的代码行.
    """
    return sys._getframe(backstep + 1).f_lineno  # pylint:disable=W0212

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
