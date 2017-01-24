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
:description:

"""
__all__ = ['TypeMan']


class BaseMan(object):
    """
    for netmsg types
    """
    def __init__(self):
        self._type2number = {}
        self._number2type = {}

    def register_types(self, kvs):
        """
        register types
        """
        for key_value in kvs.items():
            self._type2number[key_value[0]] = key_value[1]
            self._number2type[str(key_value[1])] = key_value[0]

    def getkey_bynumber(self, number):
        """
        get type by number
        """
        return self._number2type[str(number)]

    def getnumber_bykey(self, key):
        """
        get number by type
        """
        return self._type2number[key]

    def get_key_list(self):
        """return key list"""
        return self._type2number.keys()


class TypeMan(BaseMan):
    """
    msg flag class
    """


class FlagMan(BaseMan):
    """
    msg flag class
    """


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
