#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:descrition:
    error related module
"""

__all__ = [
    'BaseCupException', 'DecoratorException', 'LoggerException',
    'ResException', 'NoSuchProcess', 'AccessDenied', 'NetException',
    'AsyncMsgError', 'ThreadTermException', 'LockFileError',
    'NotImplementedYet'
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
        BaseCupException.__init__(self, msg)


class NoSuchProcess(ResException):
    """
    通用Exception, 找不到这个进程
    """
    def __init__(self, pid, str_process_name):
        ResException.__init__(self,
            'NoSuchProcess, pid %d, proc_name:%s' % (pid, str_process_name)
        )


class AccessDenied(ResException):
    """
    通用Exception, 权限相关的异常Exception类
    """
    def __init__(self, str_resouce):
        ResException.__init__(self,
            'Resouce access denied: %s' % str_resouce
        )


# ## Net related exceptions ####
class NetException(BaseCupException):
    """
    通用网络相关Exception
    """
    def __init__(self, msg=''):
        BaseCupException.__init__(self, msg)


class AsyncMsgError(NetException):
    """
    cup.net.async异步消息相关的异常Exception类
    """
    def __init__(self, msg=''):
        NetException.__init__(self, msg)


# ## Shell related exceptions ####
class ShellException(BaseCupException):
    """
    cup.shell相关的Exception
    """
    def __init__(self, msg=''):
        BaseCupException.__init__(self, msg)


class IOException(BaseCupException):
    """
    IO related exceptions inside cup
    """
    def __init__(self, msg=''):
        BaseCupException.__init__(self, msg)


class NoSuchFileOrDir(IOException):
    """
    文件或者目录不存在
    """
    def __init__(self, msg=''):
        IOException.__init__(self, msg)


class ThreadTermException(BaseCupException):
    """
        结束线程相关的err
    """
    def __init__(self, msg=''):
        BaseCupException.__init__(self, msg)


class NotInitialized(BaseCupException):
    """
    没有初始化
    """
    def __init__(self, msg=''):
        msg = 'Not initialized: %s' % msg
        BaseCupException.__init__(self, msg)


class LockFileError(BaseCupException):
    """
    LockFileError
    """
    def __init__(self, msg=''):
        msg = 'LockFileError: %s' % msg
        BaseCupException.__init__(self, msg)


class ExpectFailure(BaseCupException):
    """
    Expect failure for cup.unittest
    """
    def __init__(self, expect, got):
        msg = 'expect failure, expect {0}, got {1}'.format(expect, got)
        BaseCupException.__init__(self, msg)


class NotImplementedYet(BaseCupException):
    """
    Not implemented yet
    """
    def __init__(self, msg=''):
        msg = 'The functionality is not implemented yet, {0}'.format(msg)
        BaseCupException.__init__(self, msg)


class ConfigError(BaseCupException):
    """
    ConfigError
    """
    def __init__(self, msg=''):
        msg = 'Configuration Error: {0}'.format(msg)
        BaseCupException.__init__(self, msg)


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
