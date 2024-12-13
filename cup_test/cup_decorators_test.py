#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:

"""

from cup import decorators


class TestD:
    def __init__(self) -> None:
       """
       """

    def funca(self):
        """
        """
        print("test func")
    
    @classmethod
    @decorators.Singleton
    def singleton_instance(cls, firstinit=False):
        return TestD()


def test_decorator_singleton():
    a: TestD = TestD.singleton_instance(firstinit=True)
    a.funca()



# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent

