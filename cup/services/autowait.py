#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Qiang Liu, Guannan Ma
"""
:description:
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
from cup.shell import oper


def wait_until_file_exist(
    dst_path, file_name, max_wait_sec=10, interval_sec=2, recursive=False
):
    """
    wait util the file exists or the function timeout

    :param dst_path:
        searching path
    :param file_name:
        filename, support *
    :param max_wait_sec:
        max wating time until timeout
    :param interval_sec:
        check interval
    :param recursive:
        recursively search or not
    :return:
        True if found.
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
    wait until any line in the file matches the \
    reg_str(regular expression string)

    :param dst_file_path:
        searching path
    :param reg_str:
        regular expression string
    :param max_wait_sec:
        maximum waiting time until timeout
    :param interval_sec:
        state check interval
    :return:
        True if found
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
    wait until the process does not exist anymore or the function timeouts

    :param process_path:
        process cwd
    :param max_wait_sec:
        maximum waiting time until timeout. 10 seconds by default
    :param interval_sec:
        state check interval, 0.5 second by default
    :return:
        return True if the process disapper before timeout
    """
    process_path = os.path.abspath(process_path)
    pro_path = os.path.dirname(process_path)
    pro_name = os.path.basename(process_path)
    curr_wait_sec = 0
    while curr_wait_sec < max_wait_sec:
        if not oper.is_proc_exist(pro_path, pro_name):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_process_exist(
    process_path, max_wait_sec=10, interval_sec=0.5
):
    """
    wait until the process exists

    :param process_path:
        the specific process working path
    :param max_wait_sec:
        maximum waiting time until timeout
    :param interval_sec:
        state check interval
    :return:
        return True if the process is found before timeout
    """
    process_path = os.path.abspath(process_path)
    pro_path = os.path.dirname(process_path)
    pro_name = os.path.basename(process_path)
    curr_wait_sec = 0
    while curr_wait_sec < max_wait_sec:
        if oper.is_proc_exist(pro_path, pro_name):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_port_used(
    port, max_wait_sec=10, interval_sec=0.5
):
    """
    wait until the port is used.  *Notice this function will invoke\
    a bash shell to execute command [netstat]!*

    :return:
        return True if the port is used
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if oper.is_port_used(port):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_port_not_used(
    port, max_wait_sec=10, interval_sec=0.5
):
    """
    wait until the port is free

    :return:
        return True if the port is free before timeout
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        if not oper.is_port_used(port):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def wait_until_process_used_ports(
    process_path, ports, max_wait_sec=10, interval_sec=0.5
):
    """
    wait until the process has taken the ports before timeouts

    :return:
        True if all ports are used by the specific process.
        False, otherwise
    """
    curr_wait_sec = 0

    while curr_wait_sec < max_wait_sec:
        used_port_num = 0
        for curr_port in ports:
            if oper.is_process_used_port(process_path, curr_port):
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
    wait until the [process] does not exists and all [ports] are free

    :param process_path:
        process cwd
    :param ports:
        port list
    :param interval_sec:
        state check interval
    :return:
        True if all conditions meet.
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
            if not oper.is_process_used_port(process_path, curr_port):
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
    wait until function return [boolean]
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
    check if any line matches the reg_str

    :param file_reader:
        FileReade Object
    :return:
        return True if found
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
        read from last position

        :param max_read_size:
            maximum reading length
        :return:
            content read
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
