#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    TypeMan and FlagMan is for someone who looks up value by key and
    the reverse (key by value)

"""
__all__ = ['BaseMan', 'TypeMan', 'FlagMan']


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
    msg flag class inherited from cup.flag.BaseMan
    """


class FlagMan(BaseMan):
    """
    msg flag class inherited from cup.flag.BaseMan inherited from
    cup.flag.BaseMan
    """


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
