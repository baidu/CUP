#!/usr/bin/python
# -*- coding: utf-8 -*
# Authors: shouc (https://github.com/shouc)
# Modifier: Guannan Ma (@mythmgn)
# copyright:
#    Copyright [CUP] - See LICENSE for details.
"""
query mac resource module
"""
from __future__ import print_function
import os
import time
import collections

import psutil

from cup import unittest
from cup import decorators


__all__ = [
    'get_kernel_version', 'get_cpu_nums',
    'get_disk_usage_all', 'get_disk_info'
]

_CPU_COLUMNS = [
    'usr',
    'nice',
    'system',
    'idle'
]
_MEM_COLUMNS = [
    'total',
    'avail',
    'percent',
    'used',
    'free',
    'active',
    'inactive',
    'wired'
]


class CPUInfo(collections.namedtuple('CPUInfo', _CPU_COLUMNS)):
    """
    CPUInfo is used for get_cpu_usage function. The following attr will be
    in the namedtuple:
    usr,
    nice,
    system,
    idle

    I.g.
    ::

        import cup
        # count cpu usage
        from cup.res import linux
        cpuinfo = mac.get_cpu_usage(intvl_in_sec=60)
        print cpuinfo.usr
    """


class MemInfo(collections.namedtuple('vmem', _MEM_COLUMNS)):
    """
    MemInfo
    wired (BSD, macOS): memory that is marked to always stay in RAM.
                It is never moved to disk.
    """


def get_kernel_version():
    """
    get kernel info of mac.
    e.g.('16', '7', '0'):
    """
    @decorators.needmac
    def _get_kernel_version():
        versions = os.uname()[2]
        return tuple([info for info in versions.split('.')])
    return _get_kernel_version()


def get_cpu_nums():
    """
    return cpu num
    """
    @decorators.needmac
    def _get_cpu_nums():
        return os.sysconf("SC_NPROCESSORS_ONLN")
    return _get_cpu_nums()


def get_disk_usage_all(raw=False):
    """
    :param raw:
        measure set to Byte if Raw is True
    :return:
        a py dict: { 'totalSpace': xxx, 'usedSpace': xxx, 'freeSpace': xxx,
        'unit': xxx
        }
    """
    @decorators.needmac
    def _get_disk_usage_all(raw=False):
        byte2gb = 1024 * 1024 * 1024
        byte2mb = 1024 * 1024
        stat = os.statvfs("/")
        free = stat.f_bavail * stat.f_frsize
        total = stat.f_blocks * stat.f_frsize
        unit = "Byte"
        if not raw:
            if total > byte2gb:
                free, total = \
                    free / byte2gb, total / byte2gb
                unit = "GB"
            elif total > byte2mb:
                free, total = \
                    free / byte2mb, total / byte2mb
                unit = "MB"
        return {
            "totalSpace": total,
            "usedSpace": total - free,
            "freeSpace": free,
            "unit":unit
        }
    return _get_disk_usage_all(raw)


def get_disk_info():
    """
    :return:
        get disk info from the current macOS

    :raise Exception:
        RuntimeError, if got no disk at all
    """
    @decorators.needmac
    def _get_disk_info():
        info = os.popen("df -lh")
        all_diskinfo = []
        for line in enumerate(info.readlines()):
            if line[0] != 0:
                blockinfo = []
                for block in line[1].split(" "):
                    if len(block) != 0:
                        blockinfo.append(block)
                all_diskinfo.append({
                    "FileSystem":  blockinfo[0],
                    "Size":        blockinfo[1],
                    "Used":        blockinfo[2],
                    "Available":   blockinfo[3],
                    "Percentage":  blockinfo[4],
                    })
            else:
                continue
        try:
            return all_diskinfo
        except:
            raise RuntimeError("couldn't find disk")



def get_cpu_usage(intvl_in_sec=1):
    """
    get cpu usage statistics during a time period (intvl_in_sec), return a
    namedtuple CPUInfo
    """
    unittest.assert_gt(intvl_in_sec, 0)
    ret = []
    for i in range(0, len(_CPU_COLUMNS)):
        ret.append(0)
    cpu_info0 = psutil.cpu_times()
    time.sleep(intvl_in_sec)
    cpu_info1 = psutil.cpu_times()
    total = float(0.0)
    for i in range(0, len(cpu_info1)):
        minus = float(cpu_info1[i]) - float(cpu_info0[i])
        total = total + minus
        ret[i] = minus

    for i in range(0, len(ret)):
        ret[i] = ret[i] * 100 / total
    return CPUInfo(*ret)


def get_meminfo():
    """get mem info of mac"""
    meminfo = psutil.virtual_memory()
    return MemInfo(
        meminfo.total,
        meminfo.available,
        meminfo.percent,
        meminfo.used,
        meminfo.free,
        meminfo.active,
        meminfo.inactive,
        meminfo.wired
    )


def get_net_through(str_interface):
    """
    get net through

    Raise ValueError if interface does not exists
    """
    try:
        net_trans = psutil.net_io_counters(True)[str_interface]
    except KeyError:
        raise ValueError('interface {0} not exist'.format(str_interface))
    return (int(net_trans.bytes_recv), int(net_trans.bytes_sent))


def get_net_transmit_speed(str_interface, intvl_in_sec=1):
    """get network interface write/read speed"""
    decorators.needmac(True)
    unittest.assert_gt(intvl_in_sec, 0)
    rx_bytes0 = get_net_through(str_interface)[0]
    time.sleep(intvl_in_sec)
    rx_bytes1 = get_net_through(str_interface)[0]
    return (rx_bytes1 - rx_bytes0) / intvl_in_sec


def get_net_recv_speed(str_interface, intvl_in_sec):
    """
    get average network recv-speed during a time period (intvl_in_sec)
    """
    decorators.needmac(True)
    unittest.assert_gt(intvl_in_sec, 0)
    tx_bytes0 = get_net_through(str_interface)[1]
    time.sleep(intvl_in_sec)
    tx_bytes1 = get_net_through(str_interface)[1]
    return (tx_bytes1 - tx_bytes0) / intvl_in_sec


if '__main__' == __name__:
    # system info
    print(get_cpu_nums())
    print(get_kernel_version())
    print(get_disk_usage_all())
    print(get_disk_info())
