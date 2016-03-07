#!/usr/bin/env python
# -*- coding: utf-8 -*
# #############################################################
#
#  Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#
# #############################################################
"""
:authors:
    Guannan Ma maguannan@baidu.com @mythmgn
:create_date:
    2015.09.07
:modify_date:
    2015.09.07
:description:
    for const value
"""
import cup

# pylint:disable = R0903
class _const(object):
    class ConstError(cup.err.BaseCupException):
        """
        const error
        """
        def __init__(self, msg=''):
            msg = 'Cup const error: %s.' % msg
            super(self.__class__, self).__init__(msg)

    def __setattr__(self, key, value):
        if not key.isupper():
            raise self.ConstError('Const value shoule be upper')
        if key in self.__dict__:
            raise self.ConstError('Const value cannot be changed')
        self.__dict__[key] = value

# you can access CUP const like below:
# from cup import const
# print const.VERSION

import sys
# pylint: disable=C0103
# pylint: disable=C0103,W0201
_const_obj = _const()
_const_obj.VERSION = '1.4.2'
_const_obj.AUTHOR = 'nfs-qa@baidu.com'
sys.modules[__name__] = _const_obj

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
