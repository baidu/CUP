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
    context for threadpool
"""

from __future__ import division
import threading


class ContextManager(object):
    """
    函数调用上下文相关类。
    """
    def __init__(self):
        self.contexts = [{}]

    def call_with_context(self, new_context, func, *args, **kwargs):
        """
        context is a {}
        """
        self.contexts.append(new_context)
        try:
            return func(*args, **kwargs)
        finally:
            self.contexts.pop()

    def get_context(self, key):
        """
        get the context that has the key
        """
        for context in reversed(self.contexts):
            if key in context:
                return context[key]
        return None


class ContextTracker4Thread(object):
    """
    进行线程的上下文切换相关class.
    """
    def __init__(self):
        self.local_res = threading.local()

    def current_context(self):
        """
        get current context
        """
        try:
            return self.local_res.current_context
        except AttributeError:
            current = self.local_res.current_context = ContextManager()
        return current

    def call_with_context(self, context, func, *args, **kwargs):
        """
        调用函数func, 并使用当前context
        """
        return self.current_context().call_with_context(
            context, func, *args, **kwargs
        )

    def get_context(self, key):
        """
        获得某个key的对应的context
        """
        return self.current_context().get_context(key)

    def __repr__(self):
        tmpstr = ''
        stackind = 0
        contexts = self.local_res.current_context.contexts
        for i in reversed(contexts):
            tmpstr += 'Stack ind:%d' % stackind
            stackind += 1
            for key in i.keys():
                tmpstr += ' %s:%s' % (key, i[key])
            tmpstr += '\n'
        return tmpstr

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
