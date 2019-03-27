#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:desc:
    time related module. looking forward to accepting new patches
"""
from __future__ import print_function
import time

__all__ = ['get_str_now']


def get_str_now(fmt='%Y-%m-%d-%H-%M-%S'):
    """
    return string of 'now'

    :param fmt:
        print-format, '%Y-%m-%d-%H-%M-%S' by default
    """
    return str(time.strftime(fmt, time.localtime()))


if __name__ == '__main__':
    print(get_str_now())
