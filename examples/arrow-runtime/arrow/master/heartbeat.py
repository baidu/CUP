#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
:authors:
    Guannan Ma @mythmgn
:create_date:
    2016/06/07
:description:
    heartbeat service
"""

from cup.services import heartbeat

class HeartbeatService(heartbeat.HeartbeatService):
    """
    heartbeat service. not in use yet
    """
    def __init__(self, judge_lost_in_sec, keep_lost=False):
        heartbeat.HeartbeatService.__init__(self, judge_lost_in_sec, keep_lost)
        self._judge_lost_in_sec = judge_lost_in_sec
        self._keep_lost = keep_lost


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
