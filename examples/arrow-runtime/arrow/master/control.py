#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
:authors:
    Guannan Ma @mythmgn
:create_date:

"""
# import os
# import sys
# import copy
# import objgraph

# from cup import decorators
from cup import log
# from cup import net
from cup.services import executor
from cup.net.async import msgcenter
from cup.net.async import msg
from cup.services import heartbeat as hb_service
# from cup.util import conf

# from arrow.master import heartbeat
from arrow.common import settings
# from arrow.common import service

class ControlService(msgcenter.IMessageCenter):
    def __init__(self, ip, port, confdict):
        """control service of arrow master"""
        # status, 0 inited, 1 running 2 stopping, 3 stopped
        msgcenter.IMessageCenter.__init__(self, ip, port)
        self._master_ipport = (ip, port)
        self._confdict = confdict
        self._status = 0
        self._type_man = msg.CMsgType()
        self._type_man.register_types(settings.MSG_TYPE2NUM)
        self._executor = executor.ExecutionService(
            self._confdict['control']['queue_exec_thdnum'],
            self._confdict['control']['queue_delay_exe_thdnum']
        )
        self._heartbeat_service = hb_service.HeartbeatService(
            self._confdict['control']['judge_agent_dead_in_sec'],
            self._confdict['control']['keep_lost']
        )
        self._msg_recv = 0

    def _add_new_agent(self, ipaddr, port, resource=None):
        key = '%s:%s' % (ipaddr, port)
        # refresh heart for agent(str: 'ip:port')
        self._heartbeat_service.refresh(key, resource)

    def _on_heartbeat(self, netmsg):
        ip_port, _ = netmsg.get_from_addr()
        log.info(
            'receive heartbeat, msg_len:%d, msg_flag:%d, msg_src:%s, '
            'uniqid:%d' %
            (
                netmsg.get_msg_len(),
                netmsg.get_flag(),
                str(ip_port),
                netmsg.get_uniq_id()
            )
        )
        ack_msg = msg.CNetMsg(is_postmsg=True)
        ack_msg.set_from_addr(self._master_ipport, (1, 1))
        ipaddr, stub_future = netmsg.get_from_addr()
        ack_msg.set_to_addr(ipaddr, stub_future)
        ack_msg.set_flag(netmsg.get_flag())
        ack_msg.set_msg_type(self._type_man.getnumber_bytype('ACK_HEART_BEAT'))
        ack_msg.set_uniq_id(netmsg.get_uniq_id() + 1)
        ack_msg.set_body('ACK_HEART_BEAT')
        resource = hb_service.LinuxHost(name=str(self._master_ipport))
        resource.deserilize(netmsg.get_body())
        self._heartbeat_service.refresh(
            '%s:%s' % (ip_port[0], ip_port[1]), resource
        )
        self.post_msg(ack_msg)
        return

    def _do_heartbeat(self, msg):
        pass

    def _do_check_dead_agent(self):
        lost = self._heartbeat_service.get_lost()
        # schedule next handle dead_agent
        # status 2 == stopping
        if self._status != 2:
            self._executor.queue_exec(
                settings.ARROW_MASTER_DEFAULT_PARAMS['check_heartbeat_interval'],
                self._do_heartbeat,
                1,
                None
            )
        else:
            log.info(
                'ControlService is stopping. Check dead agent service'
                'exited'
            )

    def run(self):
        """run control service"""
        self._executor.run()
        # call CUP message center to run
        msgcenter.IMessageCenter.run(self)

    def stop(self):
        """stop control service"""
        msgcenter.IMessageCenter.stop(self)
        self._executor.stop()

    def handle(self, msg):
        """
        handle msg
        """
        log.debug('to handle msg in the child class')
        msg_type = msg.get_msg_type()
        src_peer, stub_future = msg.get_from_addr()
        # log.debug('got msg from: %s stub_future:%s' % (src_peer, stub_future))
        # log.debug('type of msg_type:{0}, settings msg_type:{1}'.format(
        #    type(msg_type), type(self._type_man.getnumber_bytype('HEART_BEAT'))
        # ))
        if msg_type == self._type_man.getnumber_bytype('HEART_BEAT'):
            self._executor.queue_exec(
                self._on_heartbeat,
                1,
                msg
            )
        else:
            self.default_handle(msg)


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
