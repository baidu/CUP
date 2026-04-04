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


class ObjectInterface:
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
    AFSObjectSystem implemented interface.
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
            ::

                {
                    'returncode': 0 for success, others for failure,
                    'msg': 'if any'
                }
        """

    def get(self, path, localpath):
        """
        get the object into localpath

        :return:
            ::

                {
                    'returncode': 0 for success, others for failure,
                    'msg': 'if any'
                }
        """

    def head(self, path):
        """
        get the object info

        :return:
            ::

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
            ::

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
            Shoule be dict like object {
                # required
                'ak': 'xxx',,   
                'sk' 'xxx',
                'endpoint: 'https://xxxx.com/',
                'bucket': 'xxx',              
                # optional
                'verify': False or '/path/to/public.crt file'  
            }
            
             verify: Whether or not to verify SSL certificates.  By default
             SSL certificates are verified.  You can provide the following
             values:

             * False - do not validate SSL certificates.  SSL will still be
               used (unless use_ssl is False), but SSL certificates
               will not be verified.
             * path/to/cert/bundle.pem - A filename of the CA cert bundle to
               uses.  You can specify this argument if you want to use a
               different CA cert bundle than the one used by botocore.

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
        self._verify = self._config.get('verify', False)
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
            config=self._s3_config,
            verify=self._verify
        )
        self._exception = exceptions.ClientError

    def put(self, dest, localfile):
        """
        Upload a local file to S3
        
        :param dest:
            Destination object key/path in S3 bucket (e.g., 'folder/file.txt')
        :param localfile:
            Local file path to upload
        
        :return:
            dict {
                'returncode': 0 for success, -1 for failure,
                'msg': Success/error message
            }
        
        :example:
            ::
            
                result = s3.put('data/test.txt', '/local/path/test.txt')
                if result['returncode'] == 0:
                    print('Upload successful')
        """
        ret = {
            'returncode': -1,
            'msg': 'failed to put object'
        }
        with open(localfile, 'rb') as fhandle:
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
        Delete an object from S3 bucket
        
        :param path:
            Object key/path to delete (e.g., 'folder/file.txt')
        
        :return:
            dict {
                'returncode': 0 for success, -1 for failure,
                'msg': Success/error message
            }
        
        :example:
            ::
            
                result = s3.delete('data/test.txt')
                if result['returncode'] == 0:
                    print('Delete successful')
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
        Download an object from S3 to local path
        
        :param path:
            Source object key/path in S3 (e.g., 'folder/file.txt')
        :param localpath:
            Local destination path to save the file
        
        :return:
            dict {
                'returncode': 0 for success, -1 for failure,
                'msg': Success/error message
            }
        
        :example:
            ::
            
                result = s3.get('data/test.txt', '/local/path/test.txt')
                if result['returncode'] == 0:
                    print('Download successful')
        """
        ret = {
            'returncode': 0,
            'msg': 'success'
        }
        try:
            with open(localpath, 'wb+') as fhandle:
                resp = self.__s3conn.get_object(
                    Key='{0}'.format(path),
                    Bucket=self._bucket
                )
                fhandle.write(resp['Body'].read())
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = str(error)
        return ret
    
    def get_fhandler(self, path):
        """
        Get file handler for streaming read of S3 object
        
        :param path:
            Source object key/path in S3 (e.g., 'folder/file.txt')
        
        :return:
            boto3.StreamingBody object if successful, None on failure
            The StreamingBody has methods:
            - read(size=-1): Read data from stream
            - close(): Close the stream
        
        :example:
            ::
            
                fhandler = s3.get_fhandler('data/test.txt')
                if fhandler:
                    content = fhandler.read()
                    fhandler.close()
        """
        try:
            resp = self.__s3conn.get_object(
                    Key='{0}'.format(path),
                    Bucket=self._bucket
            )
            return resp['Body']
        except Exception as err:
            log.error('failed to get fhandler {0}, err {1}'.format(path, err))
            return None

    def head(self, path):
        """
        Get metadata/information about an S3 object
        
        :param path:
            Object key/path in S3 (e.g., 'folder/file.txt')
        
        :return:
            dict {
                'returncode': 0 for success, -1 for failure,
                'msg': Success/error message,
                'objectinfo': dict containing object metadata {
                    'ContentLength': int (size in bytes),
                    'ContentType': str (MIME type),
                    'LastModified': datetime,
                    'ETag': str,
                    'Metadata': dict (user-defined metadata),
                    ... (other S3 response fields)
                } or None on failure
            }
        
        :example:
            ::
            
                result = s3.head('data/test.txt')
                if result['returncode'] == 0:
                    size = result['objectinfo']['ContentLength']
                    print(f'File size: {size} bytes')
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

    def presign(self, path, method='get_object', expires_in=3600, **kwargs):
        """
        Generate a pre-signed URL for temporary access to S3 object
        
        :param path:
            Object key/path in S3 (e.g., 'folder/file.txt')
        :param method:
            HTTP method for the pre-signed URL. Options:
            - 'get_object': For downloading/reading object (default)
            - 'put_object': For uploading/writing object
            - 'delete_object': For deleting object
            - 'head_object': For getting object metadata
        :param expires_in:
            URL expiration time in seconds (default: 3600 = 1 hour)
            Minimum: 1 second, Maximum: 604800 seconds (7 days)
        :param kwargs:
            Additional parameters passed to boto3 generate_presigned_url
            Common options:
            - Params: dict of method-specific parameters
            - HttpMethod: Override HTTP method
        
        :return:
            dict {
                'returncode': 0 for success, -1 for failure,
                'msg': Success/error message,
                'url': Pre-signed URL string (only if successful)
            }
        
        :raises ValueError:
            If method is not one of the supported methods
        
        :example:
            ::
            
                # Generate download URL
                result = s3.presign('data/test.txt', method='get_object')
                if result['returncode'] == 0:
                    download_url = result['url']
                    print(f'Download URL: {download_url}')
                
                # Generate upload URL with custom expiry
                result = s3.presign('uploads/file.txt', method='put_object', 
                                   expires_in=7200)
                if result['returncode'] == 0:
                    upload_url = result['url']
                    # Use requests.put(upload_url, data=file_content)
                
                # Generate URL with additional params
                result = s3.presign('data/file.txt', method='get_object',
                                   Params={'ResponseContentDisposition': 
                                          'attachment; filename="file.txt"'})
        """
        ret = {
            'returncode': -1,
            'msg': 'failed to generate presigned URL',
            'url': None
        }
        
        # Validate method
        supported_methods = ['get_object', 'put_object', 'delete_object', 
                            'head_object']
        if method not in supported_methods:
            ret['msg'] = 'Invalid method. Supported methods: {0}'.format(
                supported_methods)
            return ret
        
        try:
            # Generate pre-signed URL
            url = self.__s3conn.generate_presigned_url(
                ClientMethod=method,
                Params={
                    'Bucket': self._bucket,
                    'Key': '{0}'.format(path)
                },
                ExpiresIn=expires_in,
                **kwargs
            )
            
            ret['returncode'] = 0
            ret['msg'] = 'success'
            ret['url'] = url
            
            log.info('Generated presigned URL for {0} method, expires in {1}s'.format(
                method, expires_in))
            
        except Exception as error:
            ret['returncode'] = -1
            ret['msg'] = 'Failed to generate presigned URL: {0}'.format(str(error))
            log.error('Failed to generate presigned URL: {0}'.format(error))
        
        return ret

    def rmdir(self, path):
        """rmdir of a path"""
        raise err.NotImplementedYet('rmdir not supported for S3ObjectSystem')

    def create_bucket(self, bucket_name):
        """
        Create a new S3 bucket
        
        :param bucket_name:
            Name of the bucket to create (must be globally unique)
        
        :return:
            dict {
                'returncode': 0 for success, -1 for failure,
                'msg': Success/error message
            }
        
        :example:
            ::
            
                result = s3.create_bucket('my-new-bucket')
                if result['returncode'] == 0:
                    print('Bucket created successfully')
        """
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
        """
        Check if a bucket exists and get its metadata
        
        :param bucket_name:
            Name of the bucket to check
        
        :return:
            dict {
                'returncode': 0 for success, -1 for failure,
                'msg': Success/error message,
                'bucket_info': dict containing bucket metadata {
                    'ResponseMetadata': dict with HTTP headers,
                    ... (other S3 response fields)
                } or None on failure
            }
        
        :example:
            ::
            
                result = s3.head_bucket('my-bucket')
                if result['returncode'] == 0:
                    print('Bucket exists')
                    print(f'Bucket info: {result["bucket_info"]}')
        """
        ret = {
            'returncode': -1,
            'msg': 'failed to head bucket',
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
        """
        Delete an S3 bucket
        
        :param bucket_name:
            Name of the bucket to delete
        :param forcely:
            If True, delete all objects in the bucket before deleting the bucket.
            If False, bucket must be empty or deletion will fail.
            Default: False
        
        :return:
            dict {
                'returncode': 0 for success, -1 for failure,
                'msg': Success/error message
            }
        
        :example:
            ::
            
                # Delete empty bucket
                result = s3.delete_bucket('my-bucket')
                
                # Delete bucket with all its contents
                result = s3.delete_bucket('my-bucket', forcely=True)
                if result['returncode'] == 0:
                    print('Bucket deleted successfully')
        """
        ret = {
            'returncode': -1,
            'msg': 'failed to delete bucket'
        }
        try:
            if forcely:
                # First check if bucket exists
                resp = self.head_bucket(bucket_name)
                if resp['returncode'] != 0:
                    ret['msg'] = 'Bucket does not exist'
                    return ret
                
                # List and delete all objects
                res = self.__s3conn.list_objects(Bucket=bucket_name)
                if 'Contents' in res:
                    for obj in res['Contents']:
                        try:
                            self.__s3conn.delete_object(
                                Bucket=bucket_name,
                                Key=obj['Key']
                            )
                        except Exception as error:
                            ret['msg'] = 'Failed to delete object {0} in bucket: {1}'.format(
                                obj['Key'], str(error))
                            return ret
            
            # Delete the bucket itself
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
        """
        Rename/move an object (not implemented for S3)
        
        :param frompath:
            Source object key/path
        :param topath:
            Destination object key/path
        
        :return:
            Raises NotImplementedError
        
        :note:
            S3 doesn't support native rename operation. This would require
            copy + delete operations which is not implemented here.
        """
        raise err.NotImplementedYet('S3Object.rename not implemented yet')


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
            ::

                {
                    'returncode': 0 for success, others for failure,
                    'msg': 'if any'
                    'fileinfo': [
                        "-rw-rw-r-- 1 work work   201 Nov  9 17:03 __init__.py"
                    ]
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
