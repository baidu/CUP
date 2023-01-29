#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    utilization related module
"""

from cup.util import conf
from cup.util import constants
from cup.util import context
from cup.util import misc

# for downward compatibility. Recommand "from cup.services import xxx"
from cup.services import threadpool
from cup import thread
from cup.services import generator
from cup.services import autowait
CConf = conf.CConf
CConfModer = conf.CConfModer
CGeneratorMan = generator.CGeneratorMan
ThreadPool = threadpool.ThreadPool
CAck = misc.CAck


def check_type(param, expect):
    """
    deprecated. Recommand using misc.check_type in cup.util
    """
    misc.check_type(param, expect)


def check_not_none(param):
    """
    deprecated. Recommand using misc.check_not_none
    """
    misc.check_not_none(param)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
