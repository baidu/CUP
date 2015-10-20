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
:last_modify_date:
    2014
:descrition:
    error related module
"""

__all__ = [
    'BaseCupException', 'DecoratorException', 'LoggerException',
    'ResException', 'NoSuchProcess', 'AccessDenied', 'NetException',
    'AsyncMsgError', 'ThreadTermException'
]


class BaseCupException(Exception):
    """
    所有cup库Exception的基类.
    """
    def __init__(self, msg):
        self._msg = 'Cup module Exception:' + str(msg)

    def __str__(self):
        return repr(self._msg)


# ## Decorator Exceptions ####
class DecoratorException(BaseCupException):
    """
    Cup Decorator修饰符相关的异常Exception
    """
    def __init__(self, msg):
        super(self.__class__, self).__init__(msg)


# ## Log related exceptions ####
class LoggerException(BaseCupException):
    """
    cup.log相关的Exception
    """
    def __init__(self, msg):
        super(self.__class__, self).__init__(msg)


# ## Resouce related exceptions ####
class ResException(BaseCupException):
    """
    cup.res相关的Exception
    """
    def __init__(self, msg):
        super(self.__class__, self).__init__(msg)


class NoSuchProcess(ResException):
    """
    通用Exception, 找不到这个进程
    """
    def __init__(self, pid, str_process_name):
        super(self.__class__, self).__init__(
            'NoSuchProcess, pid %d, proc_name:%s' % (pid, str_process_name)
        )


class AccessDenied(ResException):
    """
    通用Exception, 权限相关的异常Exception类
    """
    def __init__(self, str_resouce):
        super(self.__class__, self).__init__(
            'Resouce access denied: %s' % str_resouce
        )


# ## Net related exceptions ####
class NetException(BaseCupException):
    """
    通用网络相关Exception
    """
    def __init__(self, msg=''):
        super(self.__class__, self).__init__(msg)


class AsyncMsgError(NetException):
    """
    cup.net.async异步消息相关的异常Exception类
    """
    def __init__(self, msg=''):
        super(self.__class__, self).__init__(msg)


# ## Shell related exceptions ####
class ShellException(BaseCupException):
    """
    cup.shell相关的Exception
    """
    def __init__(self, msg=''):
        super(self.__class__, self).__init__(msg)


class IOException(BaseCupException):
    """
    IO related exceptions inside cup
    """
    def __init__(self, msg=''):
        super(self.__class__, self).__init__(msg)


class NoSuchFileOrDir(IOException):
    """
    文件或者目录不存在
    """
    def __init__(self, msg=''):
        super(NoSuchFileOrDir, self).__init__(msg)


class ThreadTermException(BaseCupException):
    """
        结束线程相关的err
    """
    def __init__(self, msg=''):
        super(self.__class__, self).__init__(msg)


class NotInitialized(BaseCupException):
    """
    没有初始化
    """
    def __init__(self, msg=''):
        msg = 'Not initialized: %s' % msg
        super(self.__class__, self).__init__(msg)



# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
