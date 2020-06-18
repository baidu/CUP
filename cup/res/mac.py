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

from cup import decorators


__all__ = [
    'get_kernel_version', 'get_cpu_nums',
    'get_disk_usage_all', 'get_disk_info'
]


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


if '__main__' == __name__:
    # system info
    print(get_cpu_nums())
    print(get_kernel_version())
    print(get_disk_usage_all())
    print(get_disk_info())
