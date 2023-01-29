#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
misc classes for internal use
"""
import os
import sys


class CAck(object):
    """
    ack class
    """
    def __init__(self, binit=False):
        self._rev = binit

    def getack_infobool(self):
        """
        get bool info
        """
        return self._rev

    def setack_infobool(self, binit=False):
        """
        set bool info
        """
        self._rev = binit


def check_type(param, expect):
    """
    check type of the param is as the same as expect's

    :raise:
        raise TypeError if it's not the same
    """
    if type(param) != expect:
        raise TypeError('TypeError. Expect:%s, got %s' % (expect, type(param)))


def check_not_none(param):
    """
    check param is not None

    :raise:
        NameError if param is None
    """
    if param is None:
        raise NameError('The param has not been set before access')


def get_funcname(backstep=0):
    """
    get funcname of the current code line

    :param backstep:
        will go backward (one layer) from the current function call stack
    """
    # pylint: disable=W0212
    return sys._getframe(
        backstep + 1).f_code.co_name


def get_filename(backstep=0):
    """
    Get the file name of the current code line.

    :param backstep:
        will go backward (one layer) from the current function call stack
    """
    return os.path.basename(
        sys._getframe(backstep + 1).f_code.co_filename)  # pylint:disable=W0212


def get_lineno(backstep=0):
    """
    Get the line number of the current code line

    :param backstep:
        will go backward (one layer) from the current function call stack

    """
    return sys._getframe(backstep + 1).f_lineno  # pylint:disable=W0212

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
