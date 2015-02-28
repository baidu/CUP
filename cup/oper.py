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

import cup


__all__ = ['rm', 'rmrf', 'is_proc_exist', 'kill', 'backup_file']


# pylint: disable=C0103
def rm(name):
    """
    rm the file if no exception happens.
    Will not raise exception if it fails
    """
    try:
        os.remove(name)
    except OSError as e:
        cup.log.warn("rm oserror")


def rmrf(fpath):
    """
    可使用pythn自带的shutil.rmtree 不推荐使用这个函数
    :param fpath:
        删除的路径
    """
    shutil.rmtree(fpath)
    # """
    # rmrf一个path目录。 遇到symlink, 不Follow symlink.
    # """
    # try:
    #     # os.removedirs(name)
    #     if os.path.isdir(fpath):
    #         for root, dirs, files in os.walk(fpath, topdown=False):
    #             for name in files:
    #                 os.remove(os.path.join(root, name))
    #                 print  os.path.join(root, name)
    #             for name in dirs:
    #                 os.rmdir(os.path.join(root, name))
    #                 print "delete %s" % (os.path.join(root, name))
    #         os.rmdir(fpath)
    #     else:
    #         os.remove(fpath)
    # except OSError as e:
    #     print 'OSError:%s' % e


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
    path = os.path.realpath(os.path.abspath(path))
    # path = os.path.realpath(
    #   os.popen('cd ' + path + ' && pwd').read().strip()
    # )
    cmd = 'ps -ef|grep %s|grep -v grep|awk \'{print $2}\'' % (name)
    ret = cup.shell.ShellExec().run(cmd, 10)
    pids = ret['stdout'].strip().split('\n')
    if len(pids) == 0 or len(pids) == 1 and len(pids[0]) == 0:
        return False
    for pid in pids:
        cmd = 'ls -l /proc/%s/cwd|awk \'{print $11}\' ' % (pid)
        ret = cup.shell.ShellExec().run(cmd, 10)
        pid_path = ret['stdout'].strip().strip()
        if pid_path.find(path) == 0:
            # print '%s is exist: %s' % (name, path)
            return True
    return False


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

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
