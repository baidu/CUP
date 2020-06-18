#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    Object related storage
"""

import os
import abc
import time
import shutil
import ftplib
import traceback
import logging

from cup import log
from cup import err


__all__ = [
    'AFSObjectSystem', 'S3ObjectSystem', 'FTPObjectSystem',
    'LocalObjectSystem'
]


class ObjectInterface(object):
    """
    object interface, abstract class. Should not be used directly
    """
    __metaclass__ = abc.ABCMeta
    def __init__(self, config):
        """
        :param config:
            dict like config, should contains at leat
            {
                'uri': 'xxxx',
                'user': 'xxxx',   # or stands for accesskey
                'passwords': 'xxxx', # or stands for secretkey
                'extra': some_object
            }
        """
        self._config = config

    def _validate_config(self, config, keys):
        """validate config if there's any missing items"""
        ret = True
        for key in keys:
            if not key in config:
                ret = False

        return ret

    @abc.abstractmethod
    def put(self, dest, localfile):
        """
        :param dest:
            system path
        :param localfile:
            localfile

        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'
            }
        """

    @abc.abstractmethod
    def delete(self, path):
        """
        delete a file

        :param path:
            object path

        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'
            }
        """

    @abc.abstractmethod
    def get(self, path, localpath):
        """
        get the object into localpath
        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'
            }
        """

    @abc.abstractmethod
    def head(self, path):
        """
        get the object info
        :return:
           {
               'returncode': 0 for success, others for failure,
               'msg': 'if any'
               'objectinfo': {
                   'size': 1024, # at least have this one
                   'atime': 'xxxx.xx.xx', # optional
                   'mtime': 'xxxx.xx.xx', # optional
                   'ctime': 'xxxx.xx.xx', # optional
                   .......
               }
           }
        """

    @abc.abstractmethod
    def mkdir(self, path, recursive=True):
        """
        mkdir dir of a path
        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'
            }
        """

    @abc.abstractmethod
    def rmdir(self, path, recursive=True):
        """rmdir of a path

        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'
            }
        """

    @abc.abstractmethod
    def rename(self, frompath, topath):
        """rename from path to path"""


class AFSObjectSystem(ObjectInterface):
    """
    afs object
    """
    def __init__(self, config):
        """
        :param config:
            be complied with cup.util.conf.Configure2Dict().get_dict().
            Shoule be dict like object
        """
        ObjectInterface.__init__(self, config)

    def put(self, dest, localfile):
        """
        :param dest:
            system path
        :param localfile:
            localfile

        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'

            }
        """

    def delete(self, path):
        """
        delete a file

        :param path:
            object path

        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'

            }
        """

    def get(self, path, localpath):
        """
        get the object into localpath
        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'

            }

        """

    def head(self, path):
        """
        get the object info
        :return:
           {
               'returncode': 0 for success, others for failure,
               'msg': 'if any'
               'objectinfo': {
                   size: 1024,
                   .......
               }

           }
        """

    def mkdir(self, path):
        """
        mkdir dir of a path
        :return:
           {
               'returncode': 0 for success, others for failure,
               'msg': 'if any'
               'objectinfo': {
                   size: 1024,
                   .......
               }

           }
        """

    def rmdir(self, path):
        """rmdir of a path"""

    def rename(self, frompath, topath):
        """rename"""
        raise err.NotImplementedYet('AFSObjectSystem.rename')


# pylint: disable=R0902
# need to have so many
class S3ObjectSystem(ObjectInterface):
    """
    s3 object system
    """
    def __init__(self, config):
        """
        :param config:
            be complied with cup.util.conf.Configure2Dict().get_dict().
            Shoule be dict like object

        :raise:
            cup.err.ConfigError if there's any config item missing
        """
        ObjectInterface.__init__(self, config)
        required_keys = ['ak', 'sk', 'endpoint', 'bucket']
        if not self._validate_config(self._config, required_keys):
            raise err.ConfigError(str(required_keys))
        self._ak = self._config['ak']
        self._sk = self._config['sk']
        self._endpoint = self._config['endpoint']
        self._bucket = self._config['bucket']
        import boto3
        from botocore import exceptions
        from botocore import client as coreclient
        self._s3_config = coreclient.Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}
        )
        logging.getLogger('boto3').setLevel(logging.INFO)
        logging.getLogger('botocore').setLevel(logging.INFO)
        logging.getLogger('s3transfer').setLevel(logging.INFO)
        log.info('to connect to boto3')
        self.__s3conn = boto3.client(
            's3',
            aws_access_key_id=self._ak,
            aws_secret_access_key=self._sk,
            endpoint_url=self._endpoint,
            # region_name=conf_dict['region_name'],
            config=self._s3_config
        )
        self._exception = exceptions.ClientError

    def put(self, dest, localfile):
        """
        :param dest:
            system path
        :param localfile:
            localfile

        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'

            }
        """
        ret = {
            'returncode': -1,
            'msg': 'failed to put object'
        }
        with open(localfile, 'r') as fhandle:
            try:
                self.__s3conn.put_object(
                    Key='{0}'.format(dest),
                    Bucket=self._bucket,
                    Body=fhandle
                )
                ret['returncode'] = 0
                ret['msg'] = 'success'
            except self._exception as error:
                ret['returncode'] = -1
                ret['msg'] = str(error)
            return ret

    def delete(self, path):
        """
        delete a file

        :param path:
            object path

        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'

            }
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        try:
            self.__s3conn.delete_object(
                Key='{0}'.format(path),
                Bucket=self._bucket
            )
        except self._exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret

    def get(self, path, localpath):
        """
        get the object into localpath
        :return:
            {
                'returncode': 0 for success, others for failure,
                'msg': 'if any'

            }

        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        try:
            with open(localpath, 'w+') as fhandle:
                resp = self.__s3conn.get_object(
                    Key='{0}'.format(path),
                    Bucket=self._bucket
                )
                fhandle.write(resp['Body'].read())
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret

    def head(self, path):
        """
        get the object info
        :return:
           {
               'returncode': 0 for success, others for failure,
               'msg': 'if any'
               'objectinfo': {
                   size: 1024,
                   .......
               }

           }
        """
        ret = {
            'returncode': -1,
            'msg': 'failed to get objectinfo'
        }
        try:
            resp = self.__s3conn.head_object(
                Key='{0}'.format(path),
                Bucket=self._bucket
            )
            ret['objectinfo'] = resp
            ret['returncode'] = 0
            ret['msg'] = 'success'
        except self._exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret

    def mkdir(self, path):
        """
        mkdir dir of a path
        :return:
           {
               'returncode': 0 for success, others for failure,
               'msg': 'if any'
               'objectinfo': {
                   size: 1024,
                   .......
               }
           }
        """
        raise err.NotImplementedYet('mkdir not supported for S3ObjectSystem')

    def rmdir(self, path):
        """rmdir of a path"""
        raise err.NotImplementedYet('rmdir not supported for S3ObjectSystem')

    def create_bucket(self, bucket_name):
        """create bucket"""
        ret = {
            'returncode': -1,
            'msg': 'failed to create bucket'
        }
        try:
            resp = self.__s3conn.create_bucket(
                Bucket=bucket_name
            )
            ret['returncode'] = 0
            ret['msg'] = 'success'
        except self._exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret

    def head_bucket(self, bucket_name):
        """create bucket"""
        ret = {
            'returncode': -1,
            'msg': 'failed to create bucket',
            'bucket_info': None
        }
        try:
            resp = self.__s3conn.head_bucket(
                Bucket=bucket_name
            )
            ret['returncode'] = 0
            ret['msg'] = 'success'
            ret['bucket_info'] = resp
        except self._exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret

    def delete_bucket(self, bucket_name, forcely=False):
        """delete bucket

        :param forcely:
            if forcely is True, the bucket will be delete no matter it has
                objects inside. Otherwise, you have to delete items inside,
                then delete the bucket

        """
        ret = {
            'returncode': -1,
            'msg': 'failed to create bucket'
        }
        try:
            if forcely:
                resp = self.head_bucket(bucket_name)
                res = self.__s3conn.list_objects(Bucket=bucket_name)
                if 'Contents' in res:
                    for obj in res['Contents']:
                        try:
                            self.__s3conn.delete_object(
                                Bucket=bucket_name,
                                Key=obj['Key']
                            )
                        except Exception as error:
                            ret['msg'] = 'faield to delete obj in bucket'
                            return ret
            resp = self.__s3conn.delete_bucket(
                Bucket=bucket_name
            )
            ret['returncode'] = 0
            ret['msg'] = 'success'
        except self._exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret

    def rename(self, frompath, topath):
        """rename"""
        raise err.NotImplementedYet('AFSObjectSystem.rename')


class FTPObjectSystem(ObjectInterface):
    """
    ftp object system, Plz notice all methods of FTPObjectSystem is NOT
    thread-safe! Be careful when you use it in a service of concurrency.
    """
    def __init__(self, config):
        """
        :param config:
            {
                "uri":"ftp://host:port",
                "user":"username",
                "password":"password",
                "extra":None   //timeout:30s
            }

        :raise:
            cup.err.ConfigError if there's any config item missing
        """
        ObjectInterface.__init__(self, config)
        required_keys = ['uri', 'user', 'passwords']
        if not self._validate_config(self._config, required_keys):
            raise err.ConfigError(str(required_keys))
        self._uri = self._config['uri']
        self._user = self._config['user']
        self._passwd = self._config['passwords']
        self._extra = self._config['extra']
        self._dufault_timeout = 30
        if self._extra is not None and isinstance(self._config['extra'], int):
            self._dufault_timeout = self._extra
        log.info('to connect to ftp server')
        self._ftp_con = ftplib.FTP()
        self._host = self._uri.split(':')[1][2:]
        self._port = ftplib.FTP_PORT
        if len(self._uri.split(':')[2]) > 0:
            self._port = int(self._uri.split(':')[2])
        self._ftp_con.connect(self._host, self._port, self._dufault_timeout)
        self._ftp_con.login(self._user, self._passwd)
        self._last_optime = time.time()
        self._timeout = 15  # idle time for ftp

    def __del__(self):
        """release connect"""
        try:
            self._ftp_con.quit()
        except:
            pass

    def _check_timeout(self):
        """check if we need to reconnect"""
        if time.time() - self._last_optime > self._timeout:
            try:
                self._ftp_con.quit()
            except:
                pass
            self._ftp_con.connect(
                self._host, self._port, self._dufault_timeout
            )
            self._ftp_con.login(self._user, self._passwd)
        self._last_optime = time.time()

    def _get_relative_path(self, path, cwd):
        """get relative path for real actions"""
        cwd = os.path.normpath(cwd)
        path = os.path.normpath(path)
        if path.find(cwd) >= 0 and path.startswith('/'):
            path = path[len(cwd):]
        path = path.lstrip('/')
        return path

    def put(self, destfile, localfile):
        """
        :param destfile:
            ftp path for the localfile
        :param localfile:
            localfile
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        log.info('to put localfile {0} to ftp {1}'.format(localfile, destfile))
        self._check_timeout()
        cwd = self._ftp_con.pwd()
        destdir = None
        destfile = os.path.normpath(destfile)
        destfile = self._get_relative_path(destfile, cwd)
        rindex = destfile.rfind('/')
        if rindex < 0:
            destdir = cwd
            file_name = destfile
        elif rindex >= (len(destfile) - 1):
            raise ValueError('value error, destfile {0}'.format(
                destfile))
        else:
            destdir = destfile[:rindex]
            file_name = destfile.split('/')[-1]
        log.info('put localfile {0} into ftp {1}'.format(localfile, destfile))
        with open(localfile, 'rb') as fhandle:
            try:
                self._ftp_con.cwd(destdir)
                ftp_cmd = 'STOR {0}'.format(file_name)
                self._ftp_con.storbinary(ftp_cmd, fhandle)
            except Exception as error:
                ret['returncode'] = -1
                ret['msg'] = 'failed to put, err:{0}'.format(error)
        self._ftp_con.cwd(cwd)
        return ret

    def delete(self, path):
        """delete file"""
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        log.info('to delete ftp file: {0}'.format(path))
        self._check_timeout()
        cwd = os.path.normpath(self._ftp_con.pwd())
        path = self._get_relative_path(path, cwd)
        try:
            self._ftp_con.delete(path)
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret

    def get(self, path, localpath):
        """
        get a file into localpath
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        log.info('to get ftp file {0} to  {1}'.format(path, localpath))
        self._check_timeout()
        cwd = self._ftp_con.pwd()
        path = self._get_relative_path(path, cwd)
        if localpath.endswith('/'):
            localpath += path.split('/')[-1]
        log.info('to get ftp {0} to local {1}'.format(path, localpath))
        try:
            with open(localpath, 'w+') as fhandle:
                ftp_cmd = 'RETR {0}'.format(path)
                resp = self._ftp_con.retrbinary(ftp_cmd, fhandle.write)
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to get {0} to {1}, err:{2}'.format(
                path, localpath, error
            )
            log.error(ret['msg'])
        return ret

    def head(self, path):
        """
        get the file info
        :return:
           {
               'returncode': 0 for success, others for failure,
               'msg': 'if any'
               'fileinfo': [
                   "-rw-rw-r-- 1 work work   201 Nov  9 17:03 __init__.py"
               [
           }

        """
        ret = {
            'returncode': -1,
            'msg': 'failed to get objectinfo'
        }
        self._check_timeout()
        cwd = self._ftp_con.pwd()
        path = self._get_relative_path(path, cwd)
        res_info = []
        f_flag = False
        def _call_back(arg):
            if f_flag and arg.split()[-1].strip() == file_name:
                return res_info.append(arg)
            if not f_flag:
                res_info.append(arg)
        try:
            if self.is_file(path):
                file_name = path[path.rfind('/') + 1:]
                f_flag = True
                pos = path.rfind('/')
                p_path = path[0: pos]
                self._ftp_con.cwd(p_path)
            else:
                self._ftp_con.cwd(path)

            self._ftp_con.retrlines('LIST', _call_back)
            ret['fileinfo'] = res_info
            ret['returncode'] = 0
            ret['msg'] = 'success'
            self._ftp_con.cwd(cwd)
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret

    def mkdir(self, path, recursive=True):
        """
        mkdir
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        self._check_timeout()
        cwd = self._ftp_con.pwd()
        path = self._get_relative_path(path, cwd)
        try:
            if not recursive:
                self._ftp_con.mkd(path)
            else:
                subdirs = path.split('/')
                for subdir in subdirs:
                    try:
                        self._ftp_con.cwd(subdir)
                    except Exception as e:
                        self._ftp_con.mkd(subdir)
                        self._ftp_con.cwd(subdir)
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to mkdir, err:{0}'.format(error)
        self._ftp_con.cwd(cwd)
        return ret

    def rmdir(self, path, recursive=True):
        """
        rmdir
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        self._check_timeout()
        cwd = self._ftp_con.pwd()
        path = self._get_relative_path(path, cwd)
        try:
            if not recursive:
                self._ftp_con.rmd(path)
            else:
                cwd =  self._ftp_con.pwd()
                self._ftp_con.cwd(path)
                allItems = self._ftp_con.nlst()
                for item in allItems:
                    if self.is_file(item):
                        self._ftp_con.delete(item)
                    else:
                        self.rmdir(item)
                self._ftp_con.cwd(cwd)
                self._ftp_con.rmd(path)
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to rmdir, err:{0}'.format(error)
        self._ftp_con.cwd(cwd)
        return ret

    def is_file(self, path):
        """path is file or not"""
        res = False
        self._check_timeout()
        cwd = self._ftp_con.pwd()
        path = self._get_relative_path(path, cwd)
        res_info = []
        def _call_back(arg):
            res_info.append(arg)
        try:
            self._ftp_con.cwd(path)
            self._ftp_con.cwd(cwd)
            return res
        except Exception as e:
            pass
        try:
            pos = path.rfind('/')
            if pos == -1:
                file_name = path
            else:
                p_path = path[0: pos]
                file_name = path[pos + 1:]
                self._ftp_con.cwd(p_path)
            self._ftp_con.retrlines('MLSD', _call_back)
            for item in res_info:
                if item.split(';')[-1].strip() == file_name and 'type=file' in item:
                    self._ftp_con.cwd(cwd)
                    return True
            self._ftp_con.cwd(cwd)
        except Exception as error:
            pass
        return False

    def rename(self, frompath, topath):
        """rename frompath to path"""
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        try:
            self._ftp_con.rename(frompath, topath)
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to rename from {0} to {1}'.format(
                frompath, topath
            )
        return ret


class LocalObjectSystem(ObjectInterface):
    """local object system"""

    def __init__(self, kvconfig=None):
        """
        initialize
        """
        config = {
            'uri': None,
            'user': None,   # or stands for accesskey
            'passwords': None, # or stands for secretkey
            'extra': None
        }
        ObjectInterface.__init__(self, config)

    def put(self, dest, localfile):
        """
        local object put == copy
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        try:
            shutil.copy2(dest, localfile)
        # pylint: disable=W0703
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to put:{0}'.format(error)
        return ret

    def delete(self, path):
        """delete a file in local"""
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        try:
            os.unlink(path)
        # pylint: disable=W0703
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to unlink file:{0}, err:{1}'.format(
                path, error
            )
        return ret

    def get(self, path, localpath):
        """
        get a file into localpath
        """
        return self.put(path, localpath)

    def head(self, path):
        """get the object info"""
        retcode = 0
        msg = 'ok'
        objectinfo = None
        if not os.path.exists(path):
            retcode = 255
            msg = 'file/dir not found'
        else:
            statinfo = os.stat(path)
            objectinfo =  {
                'size': statinfo.st_size,
                'atime': statinfo.st_atime,
                'mtime': statinfo.st_mtime,
                'ctime': statinfo.st_ctime
            }
        info_dict = {
            'returncode': retcode,
            'msg': msg,
            'objectinfo': objectinfo
        }
        return info_dict

    def mkdir(self, path, recursive=True):
        """
        mkdir
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        func = os.makedirs
        if not recursive:
            func = os.mkdir
        try:
            func(path)
        except IOError as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to mkdir, err:{0}'.format(error)
        return ret

    def rmdir(self, path, recursive=True):
        """
        rmdir
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        func = os.rmdir
        if recursive:
            func = shutil.rmtree
        try:
            func(path)
        except IOError as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to rmdir, err:{0}'.format(error)
        return ret

    def rename(self, frompath, topath):
        """rename from path to path"""
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        try:
            os.rename(frompath, topath)
        except IOError as error:
            ret['returncode'] = -1
            ret['msg'] = 'failed to rename {0} to {1}'.format(
                frompath, topath
            )
        return ret

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
