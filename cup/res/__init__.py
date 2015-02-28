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
    resource related module
"""

import sys

if sys.platform.startswith('linux'):
    from cup.res import linux
    # from cup.res.linux import get_boottime_since_epoch as get_sys_boot_time
    # from cup.res.linux import get_boottime_since_epoch
    # from cup.res.linux import get_cpu_nums
    # from cup.res.linux import get_kernel_version
    # # resouce info
    # from cup.res.linux import get_cpu_usage
    # from cup.res.linux import get_meminfo
    # from cup.res.linux import get_swapinfo
    # from cup.res.linux import get_net_through
    # from cup.res.linux import get_net_transmit_speed
    # from cup.res.linux import get_net_recv_speed
    Process = linux.Process

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
