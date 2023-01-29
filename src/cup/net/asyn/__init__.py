#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    **Async Module is a tcp framework for asynchrous network msg tranfering**
"""

# TODO:
#   1. If the socket has been in a state in which it does not send or
#       recv any msg for more than 30mins. Shutdown the context.
#   2. Msg management


# Enhancement list:
#  1. If the socket has too many msg pending there.
#     and msg cannot be sent out. Consider this net link as dead.
#     and shutdown && close it
#  2. Multiple threads sending things.


# BUGS:
#   FIXED:
#       1. Send socket does not register in epoll
#       2. Peer2Context has resource competition
#       3. connection has starvation bug


# Silly mistakes that I made:
#   1. TCP context creation and deletion does not has lock. (Mainly on creation)
#   2. Net MSG queue will become very large if the network read/write speed does
#       not match.
#   3.


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
