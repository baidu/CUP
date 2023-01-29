#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    context for threadpool
"""

from __future__ import division
import threading


__all__ = [
    'ContextManager', 'ContextTracker4Thread'
]


class ContextManager(object):
    """
    context for function call stack
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
    thread switch tracker
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
        call [func] and set up a context with it
        """
        return self.current_context().call_with_context(
            context, func, *args, **kwargs
        )

    def get_context(self, key):
        """
        get the context by key
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
