#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################

"""
:author:
    Zhao Minghao
:create_date:
    2014
:last_date:
    2014
:descrition:
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
        'rm', 'rmrf', 'is_proc_exist', 'kill', 'backup_file',
        'is_process_used_port', 'is_port_used', 'is_path_contain_file',
        'contains_file'
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
    可使用pythn自带的shutil.rmtree 不推荐使用这个函数
    :param fpath:
        删除的路径
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


def is_proc_exist(path, name):
    """
    通过name找到该进程的pid. 之后通过传入的path匹配/proc进程目录底下的cwd文件，
    如果cwd也包含该path目录。 则认为proc进程存在， return True, 否则False
    :param path:
        源程序运行启动的路径
    :param name:
        源程序名称
    :return:
        存在返回True， 不存在返回False
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
    通过和is_proc_exist一样的检查顺序找到这个进程， 然后根据向该进程发送sign.
    sign不赋值， 默认 kill pid, 赋值 kill -sign pid.
    b_kill_child  是否递归删除子进程
    :param path:
        源程序运行启动的路径
    :param name:
        源程序名称
    :param sign:
        kill 程序发送的信号量， 支持空、9,、18、19
    :b_kill_child:
        杀死当前进程的时候是否递归删除子进程
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
    把srcpath目录下的filename文件备份到dstpath目录下。 备份名字变为
    dstpath/filename.label   label默认是(None), 可不传入，函数自动
    把label变成当前时间.
    如果dstpath不存在， 函数会尝试创建目录。如果创建失败， raise IOError
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
    把srcpath目录下的folder文件夹备份到dstpath目录下。 备份名字变为
    dstpath/foldername.label   label默认是(None), 可不传入，函数自动
    把label变成当前时间.
    如果dstpath不存在， 函数会尝试创建目录。如果创建失败， raise IOError
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
    """同contains_file"""
    return contains_file(dstpath, dstfile, recursive, follow_link)


def contains_file(dstpath, dstfile, recursive=False, follow_link=False):
    """
    判断目录是否存在指定的文件

    :param dstpath:
        目标目录
    :param dstfile:
        目标文件
    :param recursive:
        是否支持递归查找，默认False
    :return:
        查找成功返回True, 否则返回False
    """
    path = os.path.normpath(dstpath)
    fpath = os.path.normpath(dstfile.strip())
    fullpath = '{0}/{1}'.format(path, dstfile.strip())
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
    判断端口是否正在被使用

    :param port:
        端口号
    :return:
        查找成功返回True, 否则返回False
    """
    cmd = "netstat -nl | grep ':%s '" % (port)
    ret = cup.shell.ShellExec().run(cmd, 10)
    if 0 != ret['returncode']:
        return False
    stdout = ret['stdout'].strip()
    if 0 == len(stdout):
        return False
    else:
        return True


def is_process_used_port(process_path, port):
    """
    判断特定进程是否使用某个端口

    :param process_path:
        源程序运行启动的路径
    :param port:
        端口
    :return:
        查找成功返回True, 否则返回False
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
