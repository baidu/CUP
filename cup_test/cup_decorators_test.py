#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:

"""
from cup import decorators


@decorators.Singleton
class TestD:
    def __init__(self) -> None:
       """
       """

    def funca(self):
        """
        """
        print("test func")
    
    @decorators.Singleton
    @staticmethod
    def singleton_instance(firstinit=False):
        if firstinit:
            print('first init here')
        return TestD()


@decorators.Singleton
class TestSingleTon:
    def __init__(self) -> None:
        """
        """


class TestSingletonFunc:
    def __init__(self) -> None:
        """
        """
    
    @decorators.Singleton
    @staticmethod
    def singleton_instance():
        print('first init here')
        return TestSingletonFunc()


def test_decorator_singleton():
    a: TestD = TestD()
    a.funca()
    b: TestD = TestD()
    assert a is b
    c = TestD.singleton_instance(firstinit=False)
    assert c is a
    c = TestSingleTon()
    d = TestSingleTon()
    e = TestSingleTon()
    assert c is d
    assert e is d


# test_decorator_singleton()
a = TestSingletonFunc.singleton_instance()
b = TestSingletonFunc.singleton_instance()
assert a is b
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
