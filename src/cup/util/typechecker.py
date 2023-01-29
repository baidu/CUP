#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    check type and return True or False
"""
from cup.util import misc


def check_type(param, expect):
    """
    check type of the param is as the same as expect's

    :raise:
        raise TypeError if it's not the same
    """
    if type(param) != expect:
        raise TypeError('TypeError. Expect:%s, got %s' % (expect, type(param)))


def raise_error(param, expect_type):
    """
    raise type error if the type(param) != expect_type

    :raise:
        TypeError
    """

    misc.check_type(param, expect_type)


def raise_ifnone(param):
    """
    raise NameError if param is None

    """
    if param is None:
        raise NameError('The param has not been set before access')


def check_not_none(param):
    """
    check param is not None

    :raise:
        NameError if param is None
    """
    if param is None:
        raise NameError('The param has not been set before access')


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
