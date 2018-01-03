#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
:authors:
    Guannan Ma maguannan @mythmgn
:create_date:
    2016.5.10
:description:
    generate unique id for services
"""

from cup import decorators

@decorators.Singleton
class UniqueID(object):
    """
    generate unique id
    """
    def __init__(self, low, high, increment):
        pass

    def next(self):
        """get next unique id"""


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
