#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Zhao Minghao, Guannan Ma
"""
:description:
    shell operations related module
"""

import os
import time
import sys
import shutil
import signal
import random
import hashlib
import platform
import warnings
import datetime
import threading
# import traceback
import subprocess
# import collections


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


class Asynccontent(object):
    """
    make a Argcontent to async_run u have to del it after using it
    """
    def __init__(self):
        self.cmd = None
        self.timeout = None
        self.pid = None
        self.ret = None
        self.child_list = []
        self.__cmdthd = None
        self.__monitorthd = None
        self.__subpro = None


class ShellExec(object):  # pylint: disable=R0903
    """
    For shell command execution.

    ::
        from cup import shell
        shellexec = shell.ShellExec()
        # timeout=None will block the execution until it finishes
        shellexec.run('/bin/ls', timeout=None)
        # timeout>=0 will open non-blocking mode
        # The process will be killed if the cmd timeouts
        shellexec.run(cmd='/bin/ls', timeout=100)
    """

    def __init__(self):
        self._subpro = None
        self._subpro_data = None

    def __kill_process(self, pid):
        os.kill(pid, signal.SIGKILL)

    def kill_all_process(self, async_content):
        """
        to kill all process
        """
        for pid in async_content.child_list:
            self.__kill_process(pid)

    def get_async_run_status(self, async_content):
        """
        get the command's status
        """
        try:
            from cup.res import linux
            async_process = linux.Process(async_content.pid)
            res = async_process.get_process_status()
        except err.NoSuchProcess:
            res = "process is destructor"
        return res

    def get_async_run_res(self, async_content):
        """
        if the process is still running the res shoule be None,None,0
        """
        return async_content.ret

    def async_run(self, cmd, timeout):
        """
        async_run
        return a dict {uuid:pid}
        self.argcontent{cmd,timeout,ret,cmdthd,montor}
        timeout:returncode:999
        cmd is running returncode:-999
        """

        def _signal_handle():
            """
            signal setup
            """
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        def _target(argcontent):
            argcontent.__subpro = subprocess.Popen(
                    argcontent.cmd, shell=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=_signal_handle)
            from cup.res import linux
            parent = linux.Process(argcontent.__subpro.pid)
            children = parent.children(True)
            ret_dict = []
            for process in children:
                ret_dict.append(process)
            argcontent.child_list = ret_dict

        def _monitor(start_time, argcontent):
            while(int(time.mktime(datetime.datetime.now().timetuple())) - int(start_time) <
                    int(argcontent.timeout)):
                time.sleep(1)
                if argcontent.__subpro.poll() is not None:
                    self._subpro_data = argcontent.__subpro.communicate()
                    argcontent.ret['returncode'] = argcontent.__subpro.returncode
                    argcontent.ret['stdout'] = self._subpro_data[0]
                    argcontent.ret['stderr'] = self._subpro_data[1]
                    return
            str_warn = (
                'Shell "%s"execution timout:%d. To kill it' % (argcontent.cmd,
                    argcontent.timeout)
            )
            argcontent.__subpro.terminate()
            argcontent.ret['returncode'] = 999
            argcontent.ret['stderr'] = str_warn

            for process in argcontent.child_list:
                self.__kill_process(process)
            del argcontent.child_list[:]

        argcontent = Asynccontent()
        argcontent.cmd = cmd
        argcontent.timeout = timeout
        argcontent.ret = {
            'stdout': None,
            'stderr': None,
            'returncode': -999
        }
        argcontent.__cmdthd = threading.Thread(target=_target, args=(argcontent,))
        argcontent.__cmdthd.start()
        start_time = int(time.mktime(datetime.datetime.now().timetuple()))
        argcontent.__cmdthd.join(0.1)
        argcontent.pid = argcontent.__subpro.pid
        argcontent.__monitorthd = threading.Thread(target=_monitor,
                args=(start_time, argcontent))
        argcontent.__monitorthd.start()
        #this join should be del if i can make if quicker in Process.children
        argcontent.__cmdthd.join(0.5)
        return argcontent

    def run(self, cmd, timeout):
        """
        refer to the class description

        :param timeout:
            If the cmd is not returned after [timeout] seconds, the cmd process
            will be killed. If timeout is None, will block there until the cmd
            execution returns

        :return:
            returncode == 0 means success, while 999 means timeout
            {
                'stdout' : 'Success',
                'stderr' : None,
                'returncode' : 0
            }

        E.g.

        ::
            import cup
            shelltool = cup.shell.ShellExec()
            print shelltool.run('/bin/ls', timeout=1)
        """

        def _signal_handle():
            """
            signal setup
            """
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        def _target(cmd):
            self._subpro = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=_signal_handle
            )
            self._subpro_data = self._subpro.communicate()
        ret = {
            'stdout': None,
            'stderr': None,
            'returncode': 0
        }
        cmdthd = threading.Thread(target=_target, args=(cmd, ))
        cmdthd.start()
        cmdthd.join(timeout)
        if cmdthd.isAlive() is True:
            str_warn = (
                'Shell "%s"execution timout:%d. To kill it' % (cmd, timeout)
            )
            warnings.warn(str_warn, RuntimeWarning)
            self._subpro.terminate()
            ret['returncode'] = 999
            ret['stderr'] = str_warn
        else:
            self._subpro.wait()
            times = 0
            while self._subpro.returncode is None and times < 10:
                time.sleep(1)
                times += 1
            ret['returncode'] = self._subpro.returncode
            assert type(self._subpro_data) == tuple, \
                'self._subpro_data should be a tuple'
            ret['stdout'] = self._subpro_data[0]
            ret['stderr'] = self._subpro_data[1]
        return ret


def _do_execshell(cmd, b_printcmd=True, timeout=None):
    """
    do execshell
    """
    if timeout is not None and timeout < 0:
        raise cup.err.ShellException(
            'timeout should be None or >= 0'
        )
    if b_printcmd is True:
        print 'To exec cmd:%s' % cmd
    shellexec = ShellExec()
    return shellexec.run(cmd, timeout)


def execshell(cmd, b_printcmd=True, timeout=None):
    """
    执行shell命令，返回returncode
    """
    return _do_execshell(
        cmd, b_printcmd=b_printcmd, timeout=timeout)['returncode']


def execshell_withpipe(cmd):
    """
    Deprecated. Use ShellExec instead
    """
    res = os.popen(cmd)
    return res


def execshell_withpipe_ex(cmd, b_printcmd=True):
    """
    Deprecated. Recommand using ShellExec.
    """
    strfile = '/tmp/%s.%d.%d' % (
        'shell_env.py', int(os.getpid()), random.randint(100000, 999999)
    )
    os.mknod(strfile)
    cmd = cmd + ' 1>' + strfile + ' 2>/dev/null'
    os.system(cmd)
    if True == b_printcmd:
        print cmd
    fphandle = open(strfile, 'r')
    lines = fphandle.readlines()
    fphandle.close()
    os.unlink(strfile)
    return lines


def execshell_withpipe_str(cmd, b_printcmd=True):
    """
    Deprecated. Recommand using ShellExec.
    """
    return ''.join(execshell_withpipe_ex(cmd, b_printcmd))


def execshell_withpipe_exwitherr(cmd, b_printcmd=True):
    """
    Deprecated. Recommand using ShellExec.
    """
    strfile = '/tmp/%s.%d.%d' % (
        'shell_env.py', int(os.getpid()), random.randint(100000, 999999)
    )
    cmd = cmd + ' >' + strfile
    cmd = cmd + ' 2>&1'
    os.system(cmd)
    if b_printcmd:
        print cmd
    fhandle = open(strfile, 'r')
    lines = fhandle.readlines()
    fhandle.close()
    os.unlink(strfile)
    return lines


def is_proc_alive(procname, is_whole_word=False, is_server_tag=False, filters=False):
    """
    Deprecated. Recommand using cup.oper.is_proc_exist
    """
    # print procName
    if is_whole_word:
        cmd = "ps -ef|grep -w '%s'$ |grep -v grep" % procname
    else:
        cmd = "ps -ef|grep -w '%s' |grep -v grep" % procname

    if is_server_tag:
        cmd += '|grep -vwE "vim |less |vi |tail |cat |more "'
    if filters:
        if isinstance(filters, str):
            cmd += "|grep -v '%s'" % filters
        elif isinstance(filters, list):
            for _, task in enumerate(filters):
                cmd += "|grep -v '%s'" % task
    cmd += '|wc -l'
    rev = execshell_withpipe_str(cmd, False)
    if int(rev) > 0:
        return True
    else:
        return False


def forkexe_shell(cmd):
    """
    fork a new process to execute cmd (os.system(cmd))
    """
    try:
        pid = os.fork()
        if pid > 0:
            return
    except OSError:
        sys.exit(1)
    # os.chdir("/")
    os.setsid()
    # os.umask(0)
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        sys.exit(1)
    os.system(cmd)


def md5file(filename):
    """
    compute md5 hex value of a file, return with a string (hex-value)
    """
    if os.path.exists(filename) is False:
        raise IOError('No such file: %s' % filename)
    with open(filename, 'rb') as fhandle:
        md5obj = hashlib.md5()
        while True:
            strtmp = fhandle.read(131072)  # read 128k one time
            if len(strtmp) <= 0:
                break
            md5obj.update(strtmp)
    return md5obj.hexdigest()


def kill9_byname(strname):
    """
    kill -9 process by name
    """
    fd_pid = os.popen("ps -ef | grep -v grep |grep %s \
            |awk '{print $2}'" % (strname))
    pids = fd_pid.read().strip().split('\n')
    fd_pid.close()
    for pid in pids:
        os.system("kill -9 %s" % (pid))


def kill_byname(strname):
    """
    kill process by name
    """
    fd_pid = os.popen("ps -ef | grep -v grep |grep %s \
            |awk '{print $2}'" % (strname))
    pids = fd_pid.read().strip().split('\n')
    fd_pid.close()
    for pid in pids:
        os.system("kill -s SIGKILL %s" % (pid))


def del_if_exist(path, safemode=True):
    """
    delete the path if it exists, cannot delete root / under safemode
    """
    if safemode and path == '/':
        raise IOError('Cannot delete root path /')
    if os.path.lexists(path) is False:
        return -1
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path) or os.path.islink(path):
        os.unlink(path)
    else:
        raise IOError('Does not support deleting the type 4 the path')


def rmtree(path, ignore_errors=False, onerror=None, safemode=True):
    """
    safe rmtree.

    safemode, by default is True, which forbids:

    1. not allowing rmtree root "/"

    """
    if safemode:
        if os.path.normpath(os.path.abspath(path)) == '/':
            raise err.ShellException('cannot rmtree root / under safemode')
    if os.path.isfile(path):
        return os.unlink(path)
    else:
        return shutil.rmtree(path, ignore_errors, onerror)


def shell_diff(srcfile, dstfile):
    """
    shell diff two files, return 0 if it's the same.
    """
    cmd = 'diff %s %s' % (srcfile, dstfile)
    return os.system(cmd)


def get_pid(process_path, grep_string):
    """
    will return immediately after find the pid which matches

    1. ps -ef|grep %s|grep -v grep|grep -vE "^[vim|less|vi|tail|cat|more] "
    '|awk '{print $2}'

    2. workdir is the same as ${process_path}

    :param process_path:
        process that runs on
    :param grep_string:
        ps -ef|grep ${grep_string}
    :return:
        return None if not found. Otherwise, return the pid

    """
    cmd = (
        'ps -ef|grep \'%s\'|grep -v grep|grep -vwE "vim |less |vi |tail |cat |more "'
        '|awk \'{print $2}\''
    ) % (grep_string)
    ret = cup.shell.ShellExec().run(cmd, 10)
    pids = ret['stdout'].strip().split('\n')
    if len(pids) == 0 or len(pids) == 1 and len(pids[0]) == 0:
        return None
    for pid in pids:
        for sel_path in ["cwd", "exe"]:
            cmd = 'ls -l /proc/%s/%s|awk \'{print $11}\' ' % (pid, sel_path)
            ret = cup.shell.ShellExec().run(cmd, 10)
            pid_path = ret['stdout'].strip().strip()
            if pid_path.find(process_path) == 0:
                return pid
    return None

# end linux functionalities }}
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
