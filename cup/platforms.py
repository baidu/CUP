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
    cross-platform functions related module
"""

import platform

__all__ = [
    'is_linux',
    'is_windows'
]


def is_linux():
    """
    @return:
        True or False
    Check if you are running on Linux.
    """
    if platform.platform().startswith('Linux'):
        return True
    else:
        return False


def is_windows():
    """
    @return:
        True or False
    Check if you are running on Windows.
    """

    if platform.platform().startswith('Windows'):
        return True
    else:
        return False


def is_mac():
    """
    TODO:
    """
    pass


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
