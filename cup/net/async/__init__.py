#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################
"""
:author:
    Guannan Ma
:create_date:
    2014
:last_date:
    2014
:descrition:
    **Async Module是ython tcp异步通讯框架.**
"""

# TODO:
#  1. If the socket has been in a state in which it does not send or
#  recv any msg for more than 30mins. Shutdown the context.
# TODO:
#  2. If the socket has too many msg pending there.
#     and msg cannot be sent out. Consider this net link as dead.
#     and shutdown && close it

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
