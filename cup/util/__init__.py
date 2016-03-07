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
    utilization related module
"""

# from cup.util.conf import CConf
# from cup.util.conf import CConfModer
# from cup.util.generator import CGeneratorMan
# from cup.util.threadpool import ThreadPool

# from cup.util.misc import CAck, check_type, check_not_none


from cup.util import autowait
from cup.util import conf
from cup.util import constants
from cup.util import context
from cup.util import generator
from cup.util import misc
from cup.util import threadpool

CConf = conf.CConf
CConfModer = conf.CConfModer
CGeneratorMan = generator.CGeneratorMan
ThreadPool = threadpool.ThreadPool
CAck = misc.CAck


def check_type(param, expect):
    """
    同cup.util.misc.check_type. 请使用前者
    """
    misc.check_type(param, expect)


def check_not_none(param):
    """
    同cup.util.misc.check_type. 请使用前者
    """
    misc.check_not_none(param)


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
