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
    2013
:last_date:
    2014
:descrition:
    **Guannan just made a wraper out of pexpect.**
    The original copyright belongs to the author of pexpect module.
    See it at http://pexpect.sourceforge.net/pexpect.html

"""
import os
import sys

import cup
from cup.thirdp import pexpect


def _do_expect_ex(passwd, command, timeout=100, b_print_stdout=True):
    # ret 0 success 1 timeout others -1
    ret = 0
    try:
        pobj = pexpect.spawn('/bin/bash', ['-c', command], timeout=timeout)
        if b_print_stdout:
            pobj.logfile = sys.stdout
        i = pobj.expect(
            ['password:', 'continue connecting (yes/no)?'], timeout=timeout
        )
        if i == 0:
            pobj.sendline(passwd)
        elif i == 1:
            pobj.sendline("yes")
            pobj.expect(['password:'])
            pobj.sendline(passwd)
        ret = pobj.expect(pexpect.EOF)
    except pexpect.TIMEOUT:
        print 'Connection timeout'
        ret = 1
    except pexpect.EOF:
        print 'Connection exit'
        pobj.close()
        ret = pobj.exitstatus
    except Exception as error:
        print "Connection close", error
        ret = -1
    ret = {
        'exitstatus': ret,
        'remote_exitstatus': pobj.exitstatus,
        'result': pobj.before
    }
    if ret['exitstatus'] is None:
        if ret['remote_exitstatus'] == 0 or ret['remote_exitstatus'] is None:
            ret['exitstatus'] = 0
        else:
            ret['exitstatus'] = ret['remote_exitstatus']
    if ret['remote_exitstatus'] is None:
        if ret['exitstatus'] == 0 or ret['exitstatus'] is None:
            ret['remote_exitstatus'] = 0
        else:
            ret['remote_exitstatus'] = ret['exitstatus']

    return ret


def _do_expect(passwd, command, timeout=100, b_print_stdout=True):
    ret = _do_expect_ex(passwd, command, timeout, b_print_stdout)
    return (ret['exitstatus'], ret['result'])


def checkssh(hostname, username, passwd):
    """
    判断ssh的连通性， 成功的话返回True, 否则False
    """
    ret, rev = go(
        hostname, username, passwd, 'echo "testSSH"',
        timeout=8, b_print_stdout=False
    )
    if str(rev).strip().find('testSSH') >= 0:
        return True
    else:
        return False


def go(
    hostname, username, passwd, command='', timeout=800, b_print_stdout=True
):
    """
    回返在hostname机器上执行的shell命令结果信息
    历史兼容函数。 推荐使用go_ex
    command 有较多转义字符的，不推荐使用go，推荐使用go_with_scp

    :param timeout:
        执行命令超时时间， 默认800秒

    :return:
        类型tuple:  (ret, return_string)
        ret 是本机执行远程命令的返回值
        return_string 是远程执行这条shell的输出值
    """
    cmd = """ssh %s@%s '%s'""" % (username, hostname, command)
    return _do_expect(passwd, cmd, timeout, b_print_stdout)


def _judge_ret(ret, msg=''):
    if not (ret['exitstatus'] and ret['remote_exitstatus']):
        return True
    ret['result'] = msg + ' \n ' + ret['result']
    return False


def go_with_scp(
    hostname, username, passwd, command='',
    host_tmp='/tmp/', remote_tmp='/tmp/',
    timeout=800, b_print_stdout=True
):
    """
    回返在hostname机器上执行的shell命令结果信息,
    方式是：把command 写入本机文件，然后scp到远端机器，然后到远端执行此文件
    相比go_ex 和 go 而言，多了如下参数

    :param host_tmp:
        本次保存command内容的文件目录
    :param remote_tmp:
        远端保持command内容的文件目录
    :param timeout:
        执行命令超时时间， 默认800秒

    :return:
        dict.有 'exitstatus' 'remote_exitstatus' 'result' 三项输出内容

    """
    ret = {
        'exitstatus': -1,
        'remote_exitstatus': -1,
        'result': 'write host file fail'
    }
    tmp_filename = cup.util.CGeneratorMan().get_uniqname()
    host_file = host_tmp + '/' + tmp_filename
    remote_file = remote_tmp + '/' + tmp_filename
    with open(host_file, 'w') as fd:
        fd.write(command)
    if not os.path.exists(host_file):
        return ret
    ret = lscp(host_file, hostname, username, passwd, remote_file, timeout)
    if not _judge_ret(ret, 'scp ret:'):
        return ret
    cmd = ' sh %s ' % remote_file
    ret = go_ex(hostname, username, passwd, cmd, timeout, b_print_stdout)
    cmd = ' rm -f %s ' % host_file
    res = cup.shell.execshell(cmd, b_print_stdout)
    if res:
        ret['result'] = 'rm -f host_file fail, ret:%s' % res
        return ret
    cmd = ' rm -f %s ' % remote_file
    res = go_ex(hostname, username, passwd, cmd, 10)
    if not _judge_ret(res, 'rm -f remote_file ret:'):
        return res
    return ret


def go_ex(
    hostname, username, passwd, command='', timeout=800, b_print_stdout=True
):
    """
    回返在hostname机器上执行的shell命令结果信息,
    相比go而言， 回返信息更丰富，且按照dict方式回返.
    command 有较多转义字符的，不推荐使用go，推荐使用go_witch_scp

    :param timeout:
        执行命令超时时间， 默认800秒

    :return:
        dict.有 'exitstatus' 'remote_exitstatus' 'result' 三项输出内容

    """
    cmd = """ssh %s@%s '%s'""" % (username, hostname, command)
    ret = _do_expect_ex(passwd, cmd, timeout, b_print_stdout)
    return ret


def lscp(
    src, hostname, username, passwd, dst,
    timeout=800, b_print_stdout=True
):
    """
    拷贝src到hostname的dst目录下。

    :return:
        dict.有 'exitstatus' 'remote_exitstatus' 'result' 三项输出内容

    """
    cmd = 'scp -r %s %s@%s:%s' % (src, username, hostname, dst)
    return _do_expect_ex(passwd, cmd, timeout, b_print_stdout)


def lscp_prod(scpstr, passwd, dst_path, timeout=800, b_print_stdout=True):
    """
    兼容过去版本函数， 不推荐使用。
    """
    cmd = 'scp -r ' + scpstr + ' ' + dst_path
    return _do_expect(passwd, cmd, timeout, b_print_stdout)


def dscp(
    hostname, username, passwd, src, dst, timeout=9000, b_print_stdout=False
):
    """
    拷贝hostname, src目录到本地的dst目录。 采取scp -r的模式。

    :return:
        dict.有 'exitstatus' 'remote_exitstatus' 'result' 三项输出内容

    """
    cmd = 'scp -r %s@%s:%s %s' % (username, hostname, src, dst)
    return _do_expect_ex(passwd, cmd, timeout, b_print_stdout)
