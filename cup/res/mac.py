#!/bin/env python  pylint: disable=C0302
# -*- coding: utf-8 -*
"""
:author:
    Giampaolo Rodola of psutil
:descrition:
    The class [Process] is back ported from python open-source project
    [psutil]. Guannan finished porting in early 2014.
    Here is the original license applied.
:copyright:
    Psutil.
    Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
    Use of this source code is governed by a BSD-style license
    that can be found in the LICENSE file.
"""

import os
import re
import sys
import time
import errno
import socket
import base64
import struct
import threading
import warnings
import collections

import cup

@cup.decorators.needmac
def get_kernel_version():
    """
    拿到macOS系统的kernel信息， 回返是一个三元组
    e.g.('16', '7', '0'):
    """
    versions = os.uname()[2]
    return tuple([info for info in versions.split('.')])


@cup.decorators.needmac
def get_cpu_nums():
    """
    回返机器的CPU个数信息
    """
    return os.sysconf("SC_NPROCESSORS_ONLN")


@cup.decorators.needmac
def get_disk_usage_all(raw=False):
    """
    :param raw:
        是否返回以Byte为单位的数据，默认为False
    :return:
        拿到/目录的使用信息， 回返是一个字典
    """
    byteToGb = 1024 * 1024 * 1024
    byteToMb = 1024 * 1024
    st = os.statvfs("/")
    free = st.f_bavail * st.f_frsize 
    total = st.f_blocks * st.f_frsize 
    unit = "Byte"
    #为数据转换单位
    if not raw:
        if total > byteToGb:
            free, total = \
                free / byteToGb, total / byteToGb
            unit = "GB"
        elif total > byteToMb:
            free, total = \
                free / byteToMb, total / byteToMb
            unit = "MB"
    return {
        "totalSpace": total, 
        "usedSpace": total - free, 
        "freeSpace": free,
        "unit":unit
    }


@cup.decorators.needmac
def get_disk_info():
    """
    :return:
        拿到Linux系统的所有磁盘信息
    """
    info = os.popen("df -lh")
    allDiskInfo = []
    for line in enumerate(info.readlines()):
        if line[0] != 0:
            blockInfo = []
            for block in line[1].split(" "):
                if len(block) != 0:
                    blockInfo.append(block)
            allDiskInfo.append({
                "FileSystem":  blockInfo[0],
                "Size":        blockInfo[1],
                "Used":        blockInfo[2],
                "Available":   blockInfo[3],
                "Percentage":  blockInfo[4],
                })
        else:
            continue
    try:
        return allDiskInfo
    except:
        raise RuntimeError("couldn't find disk")
        

if '__main__' == __name__:
    # system info
    print get_cpu_nums()
    print get_kernel_version()
    print get_disk_usage_all()
    print get_disk_info()
