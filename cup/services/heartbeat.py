#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################
"""
:author:
    Guannan Ma maguannan@baidu.com @mythmgn
:create_date:
    2014
:last_date:
    2014
:descrition:
    heartbeat related module
"""

import time
from cup import log
from cup import net
from cup.res import linux

try:
    # pylint: disable=W0611
    import Queue as queue
except ImportError:
    # pylint: disable=F0401
    import queue


class Device(object):
    """
    Base class for all devices in heartbeat service
    """
    def __init__(self, name):
        """
        :param:
            the name of the device
        """
        self._name = name
        self._last_healthy = time.time()

    def get_last_healthy(self):
        """
        get last_healthy time of the device
        """
        return self._last_healthy

    def set_last_healthy(self):
        """
        set last_healthy time
        """
        log.debug('device %s set_last_healthy' % self._name)
        self._last_healthy = time.time()


class LinuxHost(Device):
    def __init__(self, name, init_this_host=False):
        """
        :param name:
            name of the LinuxHost
        :param init_this_host:
            if init_this_host is True, will initialize the object by this linux
            . Otherwise, you need to initialize it by yourself.
        """
        super(self.__class__, self).__init__(name)
        # -1 means initialized
        self._dict_info = {
            'ipaddr': '0.0.0.0',
            'cpu_idle': -1,
            'mem_inuse': -1,        # MB
            'mem_total': -1,
            'net_in':    -1,        # kb
            'net_out':   -1,      # kb
        }

        if init_this_host:
            self._dict_info['ipaddr'] = net.get_hostip()
            cupinfo = linux.get_cpu_usage(0.5)
            meminfo = linux.get_meminfo()
            # TODO   which one is the default network interface
            netinfo = linux.get_net_recv_speed(eth0)
            self._dict_info['cpu_idle'] = cpuinfo.idle
            self._dict_info['mem_inuse'] = meminfo.total - meminfo.free


    def set_linux_res_bydict(self, info_dict):
        """
            {
                'ipaddr': '10.10.10.1',
                'port':   8089,
                'cpu_idle': 50,
                'mem_inuse': 1024,        # MB
                'mem_total': 8192,
                'net_in':    8192,        # kb
                'net_out':   102400,      # kb
            }
        """
        for key in info_dict:
            if key not in self._dict_info:
                log.warn('does not have this key:%s, ignore' % key)
                continue
            self._dict_info[key] = info_dict[key]
            log.debug('linux info:%s updated, %s' % (key, info_dict[key]))

    def set_ip_port(self, ipaddr):
        """
        set ip information

        :param ipaddr:
            ipaddr should be string and something like 10.10.10.1
        """
        self._dict_info['ipaddr'] = ipaddr

    def get_ip(self):
        """
        return ip information
        """
        return self._dict_info['ipaddr']

    def set_cpu_idle(self, idle_rate):
        """
        set cpu idle rate
        """
        self._dict_info['cpu_idle'] = idle_rate

    def get_cpu_idle(self):
        """
        get cpu idle rate
        """
        return self._dict_info['cpu_idle']

    def set_mem_usage(self, mem_inuse, mem_total):
        """
        set up mem_inuse and mem_total.
        Will update any of them if it is not None.
        """
        if mem_inuse is not None:
            self._dict_info['mem_inuse'] = mem_inuse
        if mem_total is not None:
            self._dict_info['mem_total'] = mem_total

    def get_mem_info(self):
        """
        :return:
            (mem_inuse, mem_total), in MB
        """
        return (self._dict_info['mem_inuse'], self._dict_info['mem_total'])

    def set_net_usage(self, net_in, net_out):
        """
        :param net_in:
            net_in in kB/s. If net_in is None, will update nothing.
        :param net_out:
            net_out in kB/s. If net_out is None, will update nothing.
        """
        if net_in is not None:
            self._dict_info['net_in'] = net_in
        if net_out is not None:
            self._dict_info['net_out'] = net_out

    def get_net_usage(self):
        """
        :return:
            (net_in, net_out)
        """
        return (self._dict_info['net_in'], self._dict_info['net_out'])


class Process(LinuxHost):
    def __init__(self, process_name):
        self.

class HeartbeatService(object):
    """
    HeartBeat service
    """
    def __init__(self, judge_lost_in_sec, keep_lost=False):
        """
        :param judge_lost_in_sec:
            if you call function get_lost() and find that time.time()
            minus last_healthy time of the device > judge_lost_in_sec,
            the device will be marked as lost.
        :param keep_lost:
            whether we store lost deivce info
        """
        self._judge_lost = judge_lost_in_sec
        self._devices = {}
        if keep_lost:
            self._lost_devices = {}
        else:
            self._lost_devices = None

    def activate(self, key, device):
        """
        activate a device in HeartBeat Service.
        Add one if it's new to hbs.
        """
        device.set_last_healthy()
        self._devices[key] = device

    def adjust_judge_lost_time(self, time_in_sec):
        """
        adjust judge_lost_in_sec
        """
        log.info(
            'heartbeat service judge_lost_in_sec changed, old %d, new %d' % (
                self._judge_lost, time_in_sec
            )
        )
        self._judge_lost = time_in_sec
        return

    def refresh(self, key):
        """
        :param key:
            refresh the device by key
        :return:
            if key does not exist, return False
            else, fresh the last_healthy time of the device
        """
        assert type(key) == str, 'needs to be a str'
        device = self._devices.get(key)
        if device is None:
            log.warn('Device not found, key:%s' % key)
            return False
        device.set_last_healthy()
        return True

    def get_lost(self):
        now = time.time()
        lost_devices = []
        for dkey in self._devices.keys():
            device = self._devices['dkey']
            if device.get_last_healthy() - now > self._judge_lost:
                if self._lost_devices is not None:
                    self._lost_devices[dkey] = device
                del self._devices[dkey]
                lost_devices.append(device)
                log.warn('heartbeat lost, device:%s' % dkey)
        return lost_devices

    def cleanup_oldlost(self, dump_file=None):
        """
        cleanup old lost devices.

        :param dump_file:
            if dump_file is not None, we will store devices info into dump_file
            Otherwise, we will cleanup the lost devices only.
        """
        log.info('start - empty_lost devices, dump_file:%s' % dump_file)
        if self._lost_devices is None:
            log.info('end - does not keep_lost devices, return')
            return
        if dump_file is None:
            self._lost_devices = {}
            log.info('end - does not have dump_file, return')
            return
        try:
            with open(dump_file, 'w+') as fhandle:
                for dkey in self._lost_devices.keys():
                    fhandle.write(
                        'key:%s last_healthy:%d' % (
                            dkey, self._devices[dkey].get_last_healthy()
                        )
                    )
                    del self._lost_devices[dkey]
            log.info('end - empty_lost devices')
        except IOError as ioerror:
            log.warn('failed to dump lost_file, error:%s' % str(ioerror))
        return


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
