#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################

"""
:author:
    Qiang Liu
:create_date:
    2015
:last_date:
    2015
:descrition:
    auto wait related modules.
"""

__all__ = [
    'wait_until_file_exist', 'wait_until_reg_str_exist',
    "wait_until_process_not_exist", "wait_until_port_used",
    "wait_until_process_used_ports", "wait_until_port_not_used",
    "wait_until_process_exist", "wait_until_process_killed"
]

import os
import re
import time

import cup
from cup import oper


def wait_until_file_exist(
    dst_path, file_name, max_wait_sec=10, interval_sec=2, recursive=False
):
    """
    等待文件存在直到超时

    :param dst_path:
        查找的目标路径
    :param file_name:
        查找的文件名，支持扩展符号*
    :param max_wait_sec:
        最长等待时间，如果超过此时间，直接返回False,默认10s
    :param interval_sec:
        重试的间隔时间，默认2
    :param recursive:
        是否这次递归查找，默认False
    :return:
        查找成功返回True, 否则返回False
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if oper.contains_file(dst_path, file_name, recursive):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_reg_str_exist(
    dst_file_path, reg_str, max_wait_sec=10, interval_sec=0.5
):
    """
    等待正则字符串在文件存在直到超时,如果读取失败，raise IOError

    :param dst_file_path:
        查找的目标文件
    :param reg_str:
        正则字符串
    :param max_wait_sec:
        最长等待时间，如果超过此时间，直接返回False,默认10s
    :param interval_sec:
        重试的间隔时间，默认0.5s
    :return:
        查找成功返回True, 否则返回False
    """
    curr_wait_sec = 0
    file_reader = FileReader(dst_file_path)

    while curr_wait_sec < max_wait_sec:
        if __check_reg_str_contain(file_reader, reg_str):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_process_not_exist(
    process_path, max_wait_sec=10, interval_sec=0.5
):
    """
    等待特定路径的进程不存在直到超时

    :param process_path:
        进程的路径
    :param max_wait_sec:
        最长等待时间，如果超过此时间，直接返回False,默认10s
    :param interval_sec:
        重试的间隔时间，默认0.5s
    :return:
        查找成功返回True, 否则返回False
    """
    process_path = os.path.abspath(process_path)
    pro_path = os.path.dirname(process_path)
    pro_name = os.path.basename(process_path)
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if not cup.oper.is_proc_exist(pro_path, pro_name):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_process_exist(
    process_path, max_wait_sec=10, interval_sec=0.5
):
    """
    等待特定路径的进程存在直到超时

    :param process_path:
        进程的路径
    :param max_wait_sec:
        最长等待时间，如果超过此时间，直接返回False,默认10s
    :param interval_sec:
        重试的间隔时间，默认0.5s
    :return:
        查找成功返回True, 否则返回False
    """
    process_path = os.path.abspath(process_path)
    pro_path = os.path.dirname(process_path)
    pro_name = os.path.basename(process_path)
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if cup.oper.is_proc_exist(pro_path, pro_name):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_port_used(
    port, max_wait_sec=10, interval_sec=0.5
):
    """
    等待特定的端口被使用直到超时
    建议root账号执行，非root账号可能会因为权限问题导致获取不到端口
    此功能依赖于netstat

    :param port:
        端口号
    :param max_wait_sec:
        最长等待时间，如果超过此时间，直接返回False,默认10s
    :param interval_sec:
        重试的间隔时间，默认0.5s
    :return:
        查找成功返回True, 否则返回False
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if cup.oper.is_port_used(port):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_port_not_used(
    port, max_wait_sec=10, interval_sec=0.5
):
    """
    等待特定的端口未被使用直到超时
    建议root账号执行，非root账号可能会因为权限问题导致获取不到端口
    此功能依赖于netstat

    :param port:
        端口号
    :param max_wait_sec:
        最长等待时间，如果超过此时间，直接返回False,默认10s
    :param interval_sec:
        重试的间隔时间，默认0.5s
    :return:
        查找成功返回True, 否则返回False
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if not cup.oper.is_port_used(port):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_process_used_ports(
    process_path, ports, max_wait_sec=10, interval_sec=0.5
):
    """
    等待进程占用端口直到超时
    建议root账号执行，非root账号可能会因为权限问题导致获取不到端口暂用
    此功能依赖于netstat

    :param process_path:
        源程序运行启动的路径
    :param ports:
        端口号列表
    :param max_wait_sec:
        最长等待时间，如果超过此时间，直接返回False,默认10s
    :param interval_sec:
        重试的间隔时间，默认0.5s
    :return:
        查找成功返回True, 否则返回False
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        used_port_num = 0
        for curr_port in ports:
            if cup.oper.is_process_used_port(process_path, curr_port):
                used_port_num += 1
            else:
                break
        if used_port_num != len(ports):
            curr_wait_sec += interval_sec
            time.sleep(interval_sec)
        else:
            return True
    return False


def wait_until_process_killed(
    process_path, ports, max_wait_sec=10, interval_sec=0.5
):
    """
    等待进程被kill, 端口未被占用
    建议root账号执行，非root账号可能会因为权限问题导致获取不到端口
    此功能依赖于netstat

    :param process_path:
        源程序运行启动的路径
    :param ports:
        端口号列表，源程序使用的端口号(此处不判断该端口被其他程序占用的情况)
    :param max_wait_sec:
        最长等待时间，如果超过此时间，直接返回False,默认10s
    :param interval_sec:
        重试的间隔时间，默认0.5s
    :return:
        查找成功返回True, 否则返回False
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        # check process
        if False == wait_until_process_not_exist(
            process_path, max_wait_sec, interval_sec
        ):
            curr_wait_sec += interval_sec
            time.sleep(interval_sec)
            continue
        # check ports
        not_used_port_num = 0
        for curr_port in ports:
            if not cup.oper.is_process_used_port(process_path, curr_port):
                not_used_port_num += 1
            else:
                break
        if not_used_port_num != len(ports):
            curr_wait_sec += interval_sec
            time.sleep(interval_sec)
        else:
            return True
    return False


def _wait_until_return(func,
        boolean, max_wait_sec, interval_sec=0.5, *args, **kwargs
    ):
    """
    wait until function return true
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if func(*args, **kwargs) == boolean:
            return True
        else:
            time.sleep(interval_sec)
            curr_wait_sec += interval_sec
    return False


def wait_return_true(func, max_wait_sec, interval_sec=0.5, *args, **kwargs):
    """
    wait until func return true or max_wait_sec passes.
    """
    return _wait_until_return(
        func, True, max_wait_sec, interval_sec, *args, **kwargs
    )


def wait_return_false(func, max_wait_sec, interval_sec=0.5, *args, **kwargs):
    """
    wait until func return False or max_wait_sec passes.
    """
    return _wait_until_return(
        func, False, max_wait_sec, interval_sec, *args, **kwargs
    )


def __check_reg_str_contain(file_reader, reg_str):
    """
    检查文件中是否存在特定正则字符串(按行匹配)

    :param dst_file_path:
        FileReader实例
    :param reg_str:
        正则字符串
    :return:
        查找成功返回True, 否则返回False
    """
    file_content = file_reader.read()
    lines = file_content.splitlines()
    for line in lines:
        if re.search(reg_str, line):
            return True
    return False


class FileReader(object):
    """
    this class is used to read file incremental
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.pos = 0

    def read(self, max_read_size=None):
        """
        从上一次读取的位置继续读取

        :param max_read_size:
            一次读取的最大长度
        :return:
            读取的文件内容
        """
        # whether the file exist
        if not os.path.isfile(self.file_path):
            return ""
        ret = ""
        with open(self.file_path) as fp:
            fp.seek(0, os.SEEK_END)
            size = fp.tell()
            if size >= self.pos:
                fp.seek(self.pos, os.SEEK_SET)
                if (max_read_size is None) or (max_read_size > (size - self.pos)):
                    max_read_size = size - self.pos
                ret = fp.read(max_read_size)
                self.pos = self.pos + len(ret)
            else:  # may be a new file with the same name
                fp.seek(0, os.SEEK_SET)
                if (max_read_size is None) or (max_read_size > size):
                    max_read_size = size
                ret = fp.read(max_read_size)
                self.pos = len(ret)
        return ret
