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
"""

import time

__all__ = ['get_str_now']


def get_str_now(fmt='%Y-%m-%d-%H-%M-%S'):
    """
    :param fmt:
        默认不需要填写，默认='%Y-%m-%d-%H-%M-%S'. 可以更改成自己想用的string
        格式. 比如 '%Y.%m.%d.%H.%M.%S'

    """
    return str(time.strftime(fmt, time.localtime()))

if __name__ == '__main__':
    print get_str_now()
