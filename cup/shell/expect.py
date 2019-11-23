#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    **Guannan just made a wraper out of pexpect.**
    The original copyright belongs to the author of pexpect module.
    See it at http://pexpect.sourceforge.net/pexpect.html
"""
from __future__ import print_function
import os
import sys

import cup
from cup import log
from cup.thirdp import pexpect


__all__ = [
    'go', 'go_ex', 'checkssh', 'go_with_scp', 'lscp', 'dscp'
]


def _do_expect_ex(passwd, command, timeout=100, b_print_stdout=True):
    """ret 0 success 1 timeout others -1"""
    retcode = 0
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
        retcode = pobj.expect(pexpect.EOF)
    except pexpect.TIMEOUT:
        sys.stderr.write('Connection timeout\n')
        retcode = 1
    except pexpect.EOF:
        pobj.close()
        retcode = pobj.exitstatus
    except Exception as error:
        sys.stderr.write('Connection close, error:%s\n' % error)
        retcode = -1
    ret = {
        'exitstatus': retcode,
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
    """ invoke _do_expect_ex"""
    ret = _do_expect_ex(passwd, command, timeout, b_print_stdout)
    return (ret['exitstatus'], ret['result'])


def checkssh(hostname, username, passwd):
    """
    check if we can ssh to hostname. Return True if succeed, False otherwise.
    """
    _, rev = go(
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
    deprecated, recommand using go_ex or go_with_scp
    """
    cmd = """ssh %s@%s '%s'""" % (username, hostname, command)
    return _do_expect(passwd, cmd, timeout, b_print_stdout)


def _judge_ret(ret, msg=''):
    if not (ret['exitstatus'] and ret['remote_exitstatus']):
        return True
    ret['result'] = msg + ' \n ' + str(ret['result'])
    return False


def go_with_scp(
    hostname, username, passwd, command='',
    host_tmp='/tmp/', remote_tmp='/tmp/',
    timeout=800, b_print_stdout=True
):
    """
    Recommand using this function to remotely execute cmds.

    go_witch_scp will write a temp script file and scp to hostname:[host_tmp].
    Then execute it and get the result back.

    :param host_tmp:
        temp folder for keeping the temporary script file (contains the cmd)
    :param remote_tmp:
        remote temp folder for keeping the temporary script file
    :param timeout:
        timeout

    :return:
        a dict with keys ('exitstatus' 'remote_exitstatus' 'result')

    """
    ret = {
        'exitstatus': -1,
        'remote_exitstatus': -1,
        'result': 'write host file fail'
    }
    tmp_filename = cup.util.CGeneratorMan().get_uniqname()
    host_file = host_tmp + '/' + tmp_filename
    remote_file = remote_tmp + '/' + tmp_filename
    with open(host_file, 'w') as fhandle:
        fhandle.write(command)
    if not os.path.exists(host_file):
        return ret
    ret = lscp(host_file, hostname, username, passwd, remote_file, timeout, b_print_stdout)
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
    res = go_ex(hostname, username, passwd, cmd, 10, b_print_stdout)
    if not _judge_ret(res, 'rm -f remote_file ret:'):
        return res
    return ret


def go_ex(
    hostname, username, passwd, command='', timeout=800, b_print_stdout=True
):
    """
    Run [command] on remote [hostname] and return result. If you have a lot
    of escape sign in the command, recommand using go_with_scp

    :param timeout:
        execution timeout, by default 800 seconds

    :return:
        return a dict with keys ('exitstatus' 'remote_exitstatus' 'result')
    """
    cmd = """ssh %s@%s '%s'""" % (username, hostname, command)
    log.info('go_ex {0}'.format(cmd))
    ret = _do_expect_ex(passwd, cmd, timeout, b_print_stdout)
    return ret


def lscp(
    src, hostname, username, passwd, dst,
    timeout=800, b_print_stdout=True
):
    """
    copy [localhost]:src to [hostname]:[dst]

    :return:
        return a dict with keys ('exitstatus' 'remote_exitstatus' 'result')
    """
    cmd = 'scp -r %s %s@%s:%s' % (src, username, hostname, dst)
    log.info('{0}'.format(cmd))
    return _do_expect_ex(passwd, cmd, timeout, b_print_stdout)


def lscp_prod(scpstr, passwd, dst_path, timeout=800, b_print_stdout=True):
    """
    deprecated. Kept here for compatibility only.
    """
    cmd = 'scp -r ' + scpstr + ' ' + dst_path
    return _do_expect(passwd, cmd, timeout, b_print_stdout)


def dscp(
    hostname, username, passwd, src, dst, timeout=9000, b_print_stdout=False
):
    """
    copy [hostname]:[src] to [localhost]:[dst].

    :return:
        return a dict with keys ('exitstatus' 'remote_exitstatus' 'result')
    """
    cmd = 'scp -r %s@%s:%s %s' % (username, hostname, src, dst)
    return _do_expect_ex(passwd, cmd, timeout, b_print_stdout)
