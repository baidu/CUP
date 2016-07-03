#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
:authors:
    Guannan Ma @mythmgn
:create_date:

"""
# import gc
import time

# import pympler
# from pympler import summary
# from pympler import muppy

from cup import log
from cup.services import heartbeat as cuphb
from cup.services import executor
from cup import net
from cup.net.async import msgcenter
from cup.net.async import msg

from arrow.common import settings
from arrow.common import service

class ControlService(msgcenter.IMessageCenter):
    """
    control service for agent
    """
    def __init__(self, ip, port, confdict):
        msgcenter.IMessageCenter.__init__(self, ip, port)
        # service.BaseService.__init__(self)
        # status, 0 inited, 1 running 2 stopping, 3 stopped
        self._confdict = confdict
        self._status = service.ServiceStatus()
        self._status.set_status(self._status.INITED)
        self._type_man = msg.CMsgType()
        self._type_man.register_types(settings.MSG_TYPE2NUM)
        self._executor = executor.ExecutionService(
            int(self._confdict['control']['queue_exec_thdnum']),
            int(self._confdict['control']['queue_delay_exe_thdnum'])
        )
        self._agent_ipport = (ip, port)
        self._master_ipport = (
            net.get_hostip(self._confdict['control']['master_ip']),
            int(self._confdict['control']['master_port'])
        )
        self._last_heartbeat = -1

    def _send_heartbeat_loop(self):
        if self._status.get_status() != self._status.RUNNING:
            log.warn('control service will stop. stop sending heartbeat')
            return
        hostinfo = cuphb.LinuxHost(
            str(self._agent_ipport), True,
            self._confdict['control']['interface']
        )
        log.info('to create msg and send msg')
        netmsg = msg.CNetMsg(is_postmsg=True)
        netmsg.set_from_addr(self._agent_ipport, (1, 1))
        netmsg.set_to_addr(self._master_ipport, (1, 1))
        netmsg.set_flag(1)
        netmsg.set_msg_type(self._type_man.getnumber_bytype('HEART_BEAT'))
        netmsg.set_uniq_id(1)
        netmsg.set_body(hostinfo.serilize())
        self.post_msg(netmsg)
        log.info('finish queue sending heartbeat to {0}'.format(self._master_ipport))
        self._executor.delay_exec(
            int(self._confdict['control']['heartbeat_interval']) - 3,
            self._send_heartbeat_loop,
            urgency=executor.URGENCY_HIGH
        )

    def test_abc(self):
        """test network speed of cup.net.async"""
        if self._status.get_status() != self._status.RUNNING:
            log.warn('control service is not running, stop heartbeat')
            return
        netmsg = None
        hostinfo = 'a' * 128 * 1024
        while self._status.get_status() == self._status.RUNNING:
            # hostinfo = cuphb.LinuxHost(
            #     str(self._agent_ipport), True,
            #     self._confdict['control']['interface']
            # )
            netmsg = msg.CNetMsg(is_postmsg=True)
            netmsg.set_from_addr(self._agent_ipport, (1, 1))
            netmsg.set_to_addr(self._master_ipport, (1, 1))
            netmsg.set_flag(self._last_heartbeat)
            netmsg.set_msg_type(self._type_man.getnumber_bytype('HEART_BEAT'))
            netmsg.set_uniq_id(1)
            netmsg.set_body(hostinfo)
            self.post_msg(netmsg)
            # log.info('finish sending heartbeat to {0}'.format(self._master_ipport))

    def _on_recv_heartbeat_ack(self, netmsg):
        """on recv ack msg"""
        if netmsg.get_flag() == self._last_heartbeat:
            log.info(
                'got heartbeat from master:{0}'.format(netmsg.get_from_addr())
            )

    def handle(self, netmsg):
        """
        handle netmsg
        """
        log.debug('to handle msg in the child class')
        msg_type = netmsg.get_msg_type()
        src_peer, stub_future = netmsg.get_from_addr()
        log.debug('got msg from: %s stub_future:%s' % (src_peer, stub_future))
        if msg_type == self._type_man.getnumber_bytype('ACK_HEART_BEAT'):
            self._executor.queue_exec(
                self._on_recv_heartbeat_ack, executor.URGENCY_HIGH,
                netmsg
            )
        else:
            self.default_handle(msg)

    def stop(self):
        """
        stop the service
        """
        log.info('to stop the arrow agent')
        self._status.set_status(self._status.STOPPING)
        self._executor.stop()
        msgcenter.IMessageCenter.stop(self)
        self._status.set_status(self._status.STOPPED)

    def loop(self):
        """run loop"""
        self._status.set_status(self._status.RUNNING)
        self._executor.run()
        self._send_heartbeat_loop()
        if not msgcenter.IMessageCenter.run(self):
            log.error('message center error happened')
            self.stop()


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
