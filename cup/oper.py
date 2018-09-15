#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Zhao Minghao,
"""
:description:
    operations related module
"""


import os
import time
import shutil
import platform

import cup
from cup import decorators
from cup import err


# linux only import
if platform.system() == 'Linux':
    __all__ = [
        'rm', 'rmrf',
        'kill',
        'is_process_used_port', 'is_port_used', 'is_proc_exist',
        'is_proc_exist', 'is_process_running',
        'contains_file', 'backup_file'
    ]
# universal import (platform indepedent)
else:
    __all__ = [
        'contains_file', 'backup_file'
    ]


# linux functionalities {{

# pylint: disable=C0103
def rm(name):
    """
    rm the file if no exception happens.
    Will not raise exception if it fails
    """
    try:
        os.remove(name)
    except OSError as error:
        cup.log.warn("rm oserror: %s" % error)


def rmrf(fpath, safemode=True):
    """
    :param fpath:
        files/direcotry to be deleted.
    :param safemode:
        True by default. You cannot delete root / when safemode is True
    """
    @decorators.needlinux
    def _real_rmrf(fpath, safemode):
        """
        real rmrf
        """
        if safemode:
            if os.path.normpath(os.path.abspath(fpath)) == '/':
                raise err.ShellException('cannot rmtree root / under safemode')
        if os.path.isfile(fpath):
            os.unlink(fpath)
        else:
            shutil.rmtree(fpath)
    return _real_rmrf(fpath, safemode)


def is_process_running(path, name):
    """
    Judge if the executable is running by comparing /proc files.
    :platforms:
        linux only. Will raise exception if running on other platforms
    :param path:
        executable current working direcotry
    :param name:
        executable name
    :return:
        return True if the process is running. Return False otherwise.
    """
    @decorators.needlinux
    def _real_is_proc_exist(path, name):
        """
        _real_is_proc_exist
        """
        path = os.path.realpath(os.path.abspath(path))
        cmd = 'ps -ef|grep %s|grep -v "^grep "|grep -v "^vim "|grep -v "^less "|\
            grep -v "^vi "|grep -v "^cat "|grep -v "^more "|grep -v "^tail "|\
            awk \'{print $2}\'' % (name)
        ret = cup.shell.ShellExec().run(cmd, 10)
        pids = ret['stdout'].strip().split('\n')
        if len(pids) == 0 or len(pids) == 1 and len(pids[0]) == 0:
            return False
        for pid in pids:
            for sel_path in ["cwd", "exe"]:
                cmd = 'ls -l /proc/%s/%s|awk \'{print $11}\' ' % (pid, sel_path)
                ret = cup.shell.ShellExec().run(cmd, 10)
                pid_path = ret['stdout'].strip().strip()
                if pid_path.find(path) == 0:
                    # print '%s is exist: %s' % (name, path)
                    return True
        return False
    return _real_is_proc_exist(path, name)


# for compatibility. Do not delete this line:
is_proc_exist = is_process_running


def _kill_child(pid, sign):
    cmd = 'ps -ef|grep %s|grep -v grep|awk \'{print $2,$3}\'' % (pid)
    ret = cup.shell.ShellExec().run(cmd, 10)
    pids = ret['stdout'].strip().split('\n')
    for proc in pids:
        p_id = proc.split()
        if p_id[1] == pid:
            _kill_child(p_id[0], sign)
        if p_id[0] == pid:
            if len(sign) == 0:
                cup.shell.execshell('kill %s' % pid)
            elif sign == '9' or sign == '-9':
                cup.shell.execshell('kill -9 %s' % pid)
            elif sign == 'SIGSTOP' or sign == '19' or sign == '-19':
                cup.shell.execshell('kill -19 %s' % pid)
            elif sign == 'SIGCONT' or sign == '18' or sign == '-18':
                cup.shell.execshell('kill -18 %s' % pid)
            else:
                cup.log.error('sign error')


def kill(path, name, sign='', b_kill_child=False):
    """
    will judge if the process is running by calling function
    (is_process_running), then send kill signal to this process
    :param path:
        executable current working direcotry (cwd)
    :param name:
        executable name
    :param sign:
        kill sign, e.g. 9 for SIGKILL, 15 for SIGTERM
    :b_kill_child:
        kill child processes or not. False by default.
    """
    path = os.path.realpath(os.path.abspath(path))
    # path = os.path.abspath(path)
    cmd = 'ps -ef|grep %s|grep -v grep|awk \'{print $2}\'' % (name)
    ret = cup.shell.ShellExec().run(cmd, 10)
    pids = ret['stdout'].strip().split('\n')
    for pid in pids:
        cmd = 'ls -l /proc/%s/cwd|awk \'{print $11}\' ' % (pid)
        ret = cup.shell.ShellExec().run(cmd, 10)
        if ret['returncode'] != 0:
            return False
        pid_path = ret['stdout'].strip()
        if pid_path.find(path) == 0 or path.find(pid_path) == 0:
            if b_kill_child is True:
                _kill_child(pid, sign)
            if len(sign) == 0:
                cup.shell.execshell('kill %s' % pid)
            elif sign == '9' or sign == '-9':
                cup.shell.execshell('kill -9 %s' % pid)
            elif sign == 'SIGSTOP' or sign == '19' or sign == '-19':
                cup.shell.execshell('kill -19 %s' % pid)
            elif sign == 'SIGCONT' or sign == '18' or sign == '-18':
                cup.shell.execshell('kill -18 %s' % pid)
            else:
                cup.log.error('sign error')
    return True


def backup_file(srcpath, filename, dstpath, label=None):
    """
    Backup srcpath/filename to dstpath/filenamne.label.
    If label is None, cup will use time.strftime('%H:%M:S')

    :dstpath:
        will create the folder if no existence
    """
    if label is None:
        label = time.strftime('%H:%M:%S')
    if not os.path.exists(dstpath):
        os.makedirs(dstpath)
    shutil.copyfile(
        srcpath + '/' + filename, dstpath + '/' + filename + '.' + label
    )


def backup_folder(srcpath, foldername, dstpath, label=None):

    """
    same to backup_file except it's a FOLDER not a FILE.
    """
    if label is None:
        label = time.strftime('%H:%M:%S')
    if not os.path.exists(dstpath):
        os.makedirs(dstpath)
    os.rename(
        '%s/%s' % (srcpath, foldername),
        '%s/%s' % (dstpath, foldername + '.' + label)
    )


def is_path_contain_file(dstpath, dstfile, recursive=False, follow_link=False):
    """
    use contains_file instead. Kept still for compatibility purpose

    """
    return contains_file(dstpath, dstfile, recursive, follow_link)


def contains_file(dstpath, expected_name, recursive=False, follow_link=False):
    """
    judge if the dstfile is in dstpath

    :param dstpath:
        search path
    :param dstfile:
        file
    :param recursive:
        search recursively or not. False by default.
    :return:
        return True on success, False otherwise
    """
    path = os.path.normpath(dstpath)
    fpath = os.path.normpath(expected_name.strip())
    fullpath = '{0}/{1}'.format(path, expected_name.strip())
    fullpath = os.path.normpath(fullpath)
    if recursive:
        for (_, __, fnames) in os.walk(path, followlinks=follow_link):
            for filename in fnames:
                if filename == fpath:
                    return True
        return False
    else:
        if os.path.exists(fullpath):
            return True
        else:
            return False


def is_port_used(port):
    """
    judge if the port is used or not (It's not 100% sure as next second, some
    other process may steal the port as soon after this function returns)
    :platform:
        linux only (netstat command used inside)
    :param port:
        expected port
    :return:
        return True if the port is used, False otherwise
    """
    @decorators.needlinux
    def __is_port_used(port):
        """internal func"""
        cmd = "netstat -nl | grep ':%s '" % (port)
        ret = cup.shell.ShellExec().run(cmd, 10)
        if 0 != ret['returncode']:
            return False
        stdout = ret['stdout'].strip()
        if 0 == len(stdout):
            return False
        else:
            return True
    return __is_port_used(port)


def is_process_used_port(process_path, port):
    """
    judge if a process is using the port

    :param process_path:
        process current working direcotry (cwd)
    :return:
        Return True if process matches
    """
    # find the pid from by port
    cmd = "netstat -nlp | grep ':%s '|awk -F ' ' '{print $7}'|\
        cut -d \"/\" -f1" % (port)
    ret = cup.shell.ShellExec().run(cmd, 10)
    if 0 != ret['returncode']:
        return False
    stdout = ret['stdout'].strip()
    if 0 == len(stdout):
        return False
    dst_pid = stdout.strip()
    # check the path
    path = os.path.abspath(process_path)
    for sel_path in ['exe', 'cwd']:
        cmd = 'ls -l /proc/%s/%s|awk \'{print $11}\' ' % (dst_pid, sel_path)
        ret = cup.shell.ShellExec().run(cmd, 10)
        pid_path = ret['stdout'].strip().strip()
        if 0 == pid_path.find(path):
            return True
    return False

# end linux functionalities }}
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
