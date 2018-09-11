#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    Object related storage
"""

import abc
import logging

from cup import log
from cup import err


__all__ = ['AFSObjectSystem', 'S3ObjectSystem']


class ObjectInterface(object):
    """
    object interface, abstract class. Should not be used directly
    """
    __metaclass__ = abc.ABCMeta
    def __init__(self, config):
        """
        :param config:
            be complied with cup.util.conf.Configure2Dict().get_dict().
            Shoule be dict like object
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
                   size: 1024,
                   .......
               }

           }
        """

    @abc.abstractmethod
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

    @abc.abstractmethod
    def rmdir(self, path):
        """rmdir of a path"""


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
        if not self._validate_config(config, required_keys):
            raise err.ConfigError(str(required_keys))
        self._config = config
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
            'returncode': -1,
            'msg': 'failed to put object'
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
            'returncode': -1,
            'msg': 'failed to put object'
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
            'msg': 'failed to put object'
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


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
