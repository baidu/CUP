#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    cross-platform functions related module
"""

import sys
import select
import platform

__all__ = [
    'is_linux',
    'is_windows',
    'is_mac',
    'is_py2',
    'is_py3'
]


def is_linux():
    """
    Check if you are running on Linux.

    :return:
        True or False
    """
    if platform.platform().startswith('Linux'):
        return True
    else:
        return False


def is_windows():
    """
    Check if you are running on Windows.

    :return:
        True or False
    """

    if platform.platform().startswith('Windows'):
        return True
    else:
        return False


def is_mac():
    """
    is mac os
    """
    if hasattr(select, 'kqueue'):
        return True
    else:
        return False


def is_py2():
    """
    is python 2.x
    """
    if sys.version_info >= (3, 0):
        return False
    if sys.version_info < (3, 0):
        return True
    raise ValueError('cannot determine if it\'s python2')


def is_py3():
    """is python 3.x"""
    if (3, 0) <= sys.version_info <= (4, 0):
        return True
    else:
        return False

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
