#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    cross-platform functions related module
"""

import select
import platform

__all__ = [
    'is_linux',
    'is_windows',
    'is_mac'
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


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
