#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Weiyan Lin
"""
:description:
    made a wraper out of paramiko.**
    The original copyright belongs to the author of paramiko module.
    See it at http://docs.paramiko.org/en/stable/
"""
import os
import traceback
import stat

import cup
import paramiko
from paramiko import ssh_exception


__all__ = [
    'checkssh', 'go_ex', 'lscp', 'dscp', 'go_with_scp'
]


def _connect(hostname, username, passwd, timeout, port=22):
    """
    get connect
    :param hostname:
    :param username:
    :param passwd:
    :param timeout:
    :param port:
    :return:
    """
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, passwd, timeout=timeout)
    except ssh_exception.NoValidConnectionsError as e:
        print("username not exists")
    except ssh_exception.AuthenticationException as e:
        print("passwd not correct")
    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()
    return client


def _sftp_connect(hostname, username, passwd, timeout, port=22):
    """
    get sftp connect
    :param hostname:
    :param username:
    :param passwd:
    :param timeout:
    :param port:
    :return:
    """
    client = None
    sftp = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, passwd, timeout=timeout)
        sftp = paramiko.SFTPClient.from_transport(client.get_transport())
    except ssh_exception.NoValidConnectionsError as e:
        print("username not exists")
    except ssh_exception.AuthenticationException as e:
        print("passwd not correct")
    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()
    return client, sftp


def _close(client):
    """
    disconnect client
    :param client:
    :return:
    """
    try:
        client.close()
    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()


def _is_exists(path, function):
    """
    check path exists
    :param path:
    :param function:
    :return:
    """
    path = path.replace('\\', '/')
    try:
        function(path)
    except Exception as e:
        return False
    else:
        return True


def _check_local(local):
    """
    check dir exists, if not exists then make dir
    :param local:
    :return:
    """
    if not os.path.exists(local):
        try:
            os.mkdir(local)
            return True
        except IOError as err:
            print(err)
            return False


def _put(sftp, src, dst, msg=''):
    """
    put file/dir
    :param sftp:
    :param src:
    :param dst:
    :return: msg
    """
    name = os.path.basename(os.path.normpath(src))
    dst = os.path.join(dst, name).replace('\\', '/')
    if os.path.isdir(src):
        _is_exists(dst, function=sftp.mkdir)
        for file in os.listdir(src):
            src_file = os.path.join(src, file).replace('\\', '/')
            msg = _put(sftp=sftp, src=src_file, dst=dst, msg=msg)
    if os.path.isfile(src):
        try:
            sftp.put(src, dst)
        except Exception as e:
            msg += '[put] ' + src + '==>' + dst + ' failed\n'
        else:
            msg += '[put] ' + src + '==>' + dst + ' successed\n'
    return msg


def _get(sftp, src, dst, msg=''):
    """
    get file/dir
    :param sftp:
    :param src:
    :param dst:
    :return: msg
    """
    result = sftp.stat(src)
    if stat.S_ISDIR(result.st_mode):
        dirname = os.path.basename(os.path.normpath(src))
        dst = os.path.join(dst, dirname)
        _check_local(dst)
        for file in sftp.listdir(src):
            sub_remote = os.path.join(src, file).replace('\\', '/')
            msg = _get(sftp, sub_remote, dst, msg=msg)
    else:
        dst = os.path.join(dst, os.path.basename(src))
        try:
            sftp.get(src, dst)
        except IOError as err:
            msg += '[get] ' + src + '==>' + dst + ' failed\n'
        else:
            msg += '[get] ' + src + '==>' + dst + ' successed\n'
    return msg


def to_str(bytes_or_str):
    """
    把byte类型转换为str
    :param bytes_or_str:
    :return:
    """
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value


def checkssh(hostname, username, passwd):
    """
    check if we can ssh to hostname.
    :return:a dict with keys ('exitstatus', 'result') exitstatus 0 success -1 others
    """
    return go_ex(hostname, username, passwd, 'echo "testSSH"', timeout=8)


def go_ex(hostname, username, passwd, command='', timeout=600,
    b_print_stdout=True
):
    """
    execute command at remote.
    :return:a dict with keys ('exitstatus', 'result') exitstatus 0 success -1 others
    """
    ret = {
        'exitstatus': -1,
        'remote_exitstatus': -1,
        'result': '',
        'result_stderr': ''
    }
    client = _connect(hostname, username, passwd, timeout, 22)
    try:
        stdin, stdout, stderr = client.exec_command(command)
        ret['remote_exitstatus'] = stdout.channel.recv_exit_status()
        ret['exitstatus'] = 0
        ret['result'] = to_str(stdout.read())
        ret['result_stderr'] = to_str(stderr.read())
        if b_print_stdout:
            print(ret['result'])
    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()
        ret['exitstatus'] = -1
        ret['remote_exitstatus'] = -1
        ret['result_stderr'] = e
    finally:
        _close(client)
        return ret


def lscp(src, hostname, username, passwd, dst, timeout=800):
    """
    copy [localhost]:src to [hostname]:[dst]

    :return:a dict with keys ('exitstatus', 'result') exitstatus 0 success -1 others

    """
    ret = {
        'exitstatus': -1,
        'remote_exitstatus': -1,
        'result': ''
    }
    client, sftp = _sftp_connect(hostname, username, passwd, timeout, 22)
    if not client or not sftp:
        ret['result'] = 'connect remote host error'
        return ret
    if not _is_exists(src, function=os.stat):
        ret['result'] = "'" + src + "': No such file or directory in local"
        return ret
    if not _is_exists(dst, function=sftp.stat):
        ret['result'] = "'" + dst + "': No such directory at remote"
        return ret
    try:
        msg = _put(sftp, src, dst)
        ret['result'] = msg
        if msg.__contains__('failed'):
            return ret
        ret['exitstatus'] = 0
        ret['remote_exitstatus'] = 0
    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()
        ret['exitstatus'] = -1
        ret['remote_exitstatus'] = -1
    finally:
        _close(client)
        return ret


def dscp(hostname, username, passwd, src, dst, timeout=9000):
    """
    copy [hostname]:[src] to [localhost]:[dst].

    :return:
           a dict with keys ('exitstatus', 'result') exitstatus 0 success -1 others
    """
    ret = {
        'exitstatus': -1,
        'remote_exitstatus': -1,
        'result': ''
    }
    client, sftp = _sftp_connect(hostname, username, passwd, timeout, 22)
    if not client or not sftp:
        ret['result'] = 'connect remote host error'
        return ret
    if not _is_exists(src, function=sftp.stat):
        ret['result'] = "'" + src + "': No such file or directory at remote"
        return ret
    if not _is_exists(dst, function=os.stat):
        ret['result'] = "'" + dst + "': No such file or directory in local"
        return ret
    try:
        msg = _get(sftp, src, dst)
        ret['result'] = msg
        if msg.__contains__('failed'):
            return ret
        ret['exitstatus'] = 0
        ret['remote_exitstatus'] = 0
    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()
        ret['exitstatus'] = -1
        ret['remote_exitstatus'] = -1
    finally:
        _close(client)
        return ret


def _judge_ret(ret, msg=''):
    if not (ret['exitstatus']):
        return True
    ret['result'] = msg + ' \n ' + str(ret['result'])
    return False


def go_with_scp(
    hostname, username, passwd, command='',
    host_tmp='/tmp/', remote_tmp='/tmp/',
    timeout=800
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
        a dict with keys ('exitstatus', 'result')

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
    ret = lscp(host_file, hostname, username, passwd, remote_tmp, timeout)
    if not _judge_ret(ret, 'scp ret:'):
        return ret
    cmd = ' sh %s ' % remote_file
    ret = go_ex(hostname, username, passwd, cmd, timeout)
    os.unlink(host_file)
    cmd = ' rm -f %s ' % remote_file
    res = go_ex(hostname, username, passwd, cmd, 10)
    if not _judge_ret(res, 'rm -f remote_file ret:'):
        return res
    return ret

