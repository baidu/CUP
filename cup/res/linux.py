#!/bin/env python  pylint: disable=C0302
# -*- coding: utf-8 -*
# Authors: Giampaolo Rodola of psutil
#     The class [Process] is back ported from python open-source project
#     psutil. Guanna Ma back ported it to py-cup.
#     If any concern, plz contact mythmgn@gmail.com
#     Here is the original license applied.
# :Copyright - (Psutil)
#     Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
#     Use of this source code is governed by a BSD-style license
#     that can be found in the LICENSE file.
"""
Provie Linux Resource/State Info Query
"""
from __future__ import print_function
import os
import re
import sys
import time
import errno
import socket
import base64
import struct
import threading
import warnings
import collections
from functools import wraps

import cup
from cup import decorators


__all__ = [
    'boot_time', 'get_boottime_since_epoch',
    # disk info
    'get_disk_usage_all', 'get_disk_info',
    # cpu info
    'CPUInfo', 'get_cpu_usage', 'get_cpu_nums', 'get_cpu_core_usage',
    'MemInfo', 'get_meminfo',
    'SWAPINFO', 'get_swapinfo',
    'net_io_counters', 'get_net_through', 'get_net_transmit_speed',
    'pids', 'process_iter', 'Process',
    'get_kernel_version',
]

_CLOCK_TICKS = os.sysconf("SC_CLK_TCK")
_PAGESIZE = os.sysconf("SC_PAGE_SIZE")
_PROC_STATUSES = {
    "R": 'STATUS_RUNNING',
    "S": 'STATUS_SLEEPING',
    "D": 'STATUS_DISK_SLEEP',
    "T": 'STATUS_STOPPED',
    "t": 'STATUS_TRACING_STOP',
    "Z": 'STATUS_ZOMBIE',
    "X": 'STATUS_DEAD',
    "x": 'STATUS_DEAD',
    "K": 'STATUS_WAKE_KILL',
    "W": 'STATUS_WAKING'
}
_CONN_NONE = 'CONN_NONE'
_TCP_STATUSES = {
    "01": 'CONN_ESTABLISHED',
    "02": 'CONN_SYN_SENT',
    "03": 'CONN_SYN_RECV',
    "04": 'CONN_FIN_WAIT1',
    "05": 'CONN_FIN_WAIT2',
    "06": 'CONN_TIME_WAIT',
    "07": 'CONN_CLOSE',
    "08": 'CONN_CLOSE_WAIT',
    "09": 'CONN_LAST_ACK',
    "0A": 'CONN_LISTEN',
    "0B": 'CONN_CLOSING'
}


# # # # begin system infos # # # #
def get_boottime_since_epoch():
    """
    :return:
        return boot time (seconds) since epoch
    """
    decorators.needlinux(True)
    fp = open('/proc/stat', 'r')
    try:
        for line in fp:
            if line.startswith('btime'):
                return float(line.strip().split()[1])
        raise RuntimeError("line 'btime' not found")
    finally:
        fp.close()


def get_kernel_version():
    """
    get linux kernel verions, e.g.('2', '6', '32'):
    """
    decorators.needlinux(True)
    versions = os.uname()[2]
    # version = versions[0: versions.find('_')]
    return tuple([info for info in versions.split('.')])


def get_cpu_nums():
    """
    get cpu nums
    """
    decorators.needlinux(True)
    try:
        return os.sysconf("SC_NPROCESSORS_ONLN")
    except ValueError:
        # as a second fallback we try to parse /proc/cpuinfo
        num = 0
        fp = open('/proc/cpuinfo', 'r')
        try:
            lines = fp.readlines()
        finally:
            fp.close()
        for line in lines:
            if line.lower().startswith('processor'):
                num += 1

    # unknown format (e.g. amrel/sparc architectures), see:
    # http://code.google.com/p/psutil/issues/detail?id=200
    # try to parse /proc/stat as a last resort
    if num == 0:
        fp = open('/proc/stat', 'r')
        try:
            lines = fp.readlines()
        finally:
            fp.close()
        search = re.compile(r'cpu\d')
        for line in lines:
            line = line.split(' ')[0]
            if search.match(line):
                num += 1

    if num == 0:
        raise RuntimeError("couldn't determine platform's NUM_CPUS")
    return num


def get_disk_usage_all(raw=False):
    """
    :param raw:
        if raw is True, will use Byte as the measure. Automatically use
        MB/GB otherwise.

    :return:
        return a dict of disk usage
    """
    decorators.needlinux(True)
    byte2gb = 1024 * 1024 * 1024
    byte2mb = 1024 * 1024
    st = os.statvfs("/")
    free = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    unit = "Byte"
    if not raw:
        if total > byte2gb:
            free, total = \
                free / byte2gb, total / byte2gb
            unit = "GB"
        elif total > byte2mb:
            free, total = \
                free / byte2mb, total / byte2mb
            unit = "MB"
    return {
        "totalSpace": total,
        "usedSpace": total - free,
        "freeSpace": free,
        "unit":unit
    }


def get_disk_info():
    """
    :return:
        get disk info of the system
    """
    decorators.needlinux(True)
    info = os.popen("df -lh")
    allDiskInfo = []
    for line in enumerate(info.readlines()):
        if line[0] != 0:
            blockInfo = []
            for block in line[1].split(" "):
                if len(block) != 0:
                    blockInfo.append(block)
            allDiskInfo.append({
                "FileSystem":  blockInfo[0],
                "Size":        blockInfo[1],
                "Used":        blockInfo[2],
                "Available":   blockInfo[3],
                "Percentage":  blockInfo[4],
                })
        else:
            continue
    try:
        return allDiskInfo
    except:
        raise RuntimeError("couldn't find disk")


class MemInfo(collections.namedtuple('vmem', ' '.join([
        # all platforms
        'total', 'available', 'percent', 'used', 'free',
        # linux specific
        'active',
        'inactive',
        'buffers',
        'cached']))):
    """
    get_meminfo will get memory info (a namedtuple returned:
        total, available, percent, used, free,
        active,
        inactive,
        buffers,
        cached)

    E.g.:
    ::
        from cup.res import linux
        meminfo = linux.get_meminfo()
        print(meminfo.total)
        print(meminfo.available)
    """

#    user
#       (1) Time spent in user mode.
#    nice
#       (2) Time spent in user mode with low priority (nice).
#    system
#       (3) Time spent in system mode.
#    idle
#       (4) Time spent in the idle task.
#           This value should be USER_HZ times the
#           second entry in the /proc/uptime pseudo-file.
#    iowait (since Linux 2.5.41)
#       (5) Time waiting for I/O to complete.
#    irq (since Linux 2.6.0-test4)
#       (6) Time servicing interrupts.
#    softirq (since Linux 2.6.0-test4)
#       (7) Time servicing softirqs.
#    steal (since Linux 2.6.11)
#       (8) Stolen time, which is the time spent in other
#            operating systems when
#        running in a virtualized environment
#    guest (since Linux 2.6.24)
#       (9) Time spent running a virtual CPU for
#           guest operating systems under the
#           control of the Linux kernel.
#    guest_nice (since Linux 2.6.33)
#       (10) Time spent running a niced guest
#            (virtual CPU for guest operating systems under the
#            control of the Linux kernel).
_CPU_COLUMNS = [
    'usr',
    'nice',
    'system',
    'idle',
    'iowait',
    'irq',
    'softirq',
    'steal',
    'guest'
]


_COLUMN_LOCK = threading.Lock()

_COLUMN_LOCK.acquire()
if sys.platform.startswith('linux'):
    if get_kernel_version() >= ('2', '6', '33') and \
            _CPU_COLUMNS.count('guest_nice') <= 0:
        _CPU_COLUMNS.append('guest_nice')
_COLUMN_LOCK.release()


class CPUInfo(collections.namedtuple('CPUInfo', _CPU_COLUMNS)):
    """
        CPUInfo is used for get_cpu_usage function. The following attr will be
        in the namedtuple:
        usr,
        nice,
        system,
        idle,
        iowait,
        irq,
        softirq,
        steal,
        guest

        I.g.
        ::
            import cup
            # count cpu usage
            from cup.res import linux
            cpuinfo = linux.get_cpu_usage(intvl_in_sec=60)
            print cpuinfo.usr
    """


def _get_cput_by_stat(coreindex=None):
    """

    :param coreindex:
        None for all cpu cores
    """
    usr = nice = system = idle = iowait = irq = softirq = steal = \
        guest = guest_nice = float(0.0)
    fp = open('/proc/stat', 'r')
    if coreindex is None:
        match_str = 'cpu'
    else:
        match_str = 'cpu{0}'.format(coreindex)
    try:
        for line in fp:
            if line.startswith(match_str) and line.split()[0] == match_str:
                if _CPU_COLUMNS.count('guest_nice') > 0:
                    (usr, nice, system, idle, iowait, irq,
                        softirq, steal, guest, guest_nice) = line.split()[1:]
                else:
                    (usr, nice, system, idle, iowait, irq,
                        softirq, steal, guest) = line.split()[1:]
                break
    # pylint: disable=W0703
    except Exception:
        warnings.warn('Get cpuinfo failed', RuntimeWarning)
    finally:
        fp.close()

    if _CPU_COLUMNS.count('guest_nice') > 0:
        return CPUInfo(
            float(usr), float(nice), float(system),
            float(idle), float(iowait), float(irq),
            float(softirq), float(steal), float(guest), float(guest_nice)
        )
    else:
        return CPUInfo(
            usr, nice, system, idle, iowait, irq,
            softirq, steal, guest
        )


def get_cpu_usage(intvl_in_sec=1):
    """
    get cpu usage statistics during a time period (intvl_in_sec), return a
    namedtuple CPUInfo
    """
    decorators.needlinux(True)
    cup.unittest.assert_gt(intvl_in_sec, 0)
    ret = []
    for i in range(0, len(_CPU_COLUMNS)):
        ret.append(0)
    cpu_info0 = _get_cput_by_stat()
    time.sleep(intvl_in_sec)
    cpu_info1 = _get_cput_by_stat()
    total = float(0.0)
    for i in range(0, len(cpu_info1)):
        minus = float(cpu_info1[i]) - float(cpu_info0[i])
        total = total + minus
        ret[i] = minus

    for i in range(0, len(ret)):
        ret[i] = ret[i] * 100 / total
    return CPUInfo(*ret)


def get_cpu_core_usage(coreindex, intvl_in_sec=1):
    """
    :param index:
        cpu core index
    """
    decorators.needlinux(True)
    cup.unittest.assert_gt(intvl_in_sec, 0)
    ret = []
    ret = [0 for _ in _CPU_COLUMNS]
    cpu_info0 = _get_cput_by_stat(coreindex)
    time.sleep(intvl_in_sec)
    cpu_info1 = _get_cput_by_stat(coreindex)
    total = float(0.0)
    for i in range(0, len(cpu_info1)):
        minus = float(cpu_info1[i]) - float(cpu_info0[i])
        total = total + minus
        ret[i] = minus

    for i in range(0, len(ret)):
        ret[i] = ret[i] * 100 / total
    return CPUInfo(*ret)


def get_meminfo():
    """
    get system memory info
    """
    decorators.needlinux(True)
    total = free = buffers = cached = active = inactive = None
    fp = open('/proc/meminfo', 'r')
    try:
        for line in fp:
            if line.startswith('MemTotal'):
                total = int(line.split()[1]) * 1024
            elif line.startswith('MemFree'):
                free = int(line.split()[1]) * 1024
            elif line.startswith('Buffers'):
                buffers = int(line.split()[1]) * 1024
            elif line.startswith('Cached:'):
                cached = int(line.split()[1]) * 1024
            elif line.startswith('Active:'):
                active = int(line.split()[1]) * 1024
            elif line.startswith('Inactive:'):
                inactive = int(line.split()[1]) * 1024
            if cached is not None \
                and active is not None \
                    and inactive is not None:
                break
        else:
            # we might get here when dealing with exotic Linux flavors, see:
            # http://code.google.com/p/psutil/issues/detail?id=313
            msg = "'cached', 'active' and 'inactive' memory stats couldn't " \
                  "be determined and were set to 0"
            warnings.warn(msg, RuntimeWarning)
            total = free = buffers = cached = active = inactive = 0
    finally:
        fp.close()
    avail = free + buffers + cached
    used = total - free
    percent = int((total - avail) * 100 / total)
    return MemInfo(
        total,
        avail,
        percent,
        used,
        free,
        active,
        inactive,
        buffers,
        cached
    )


class SWAPINFO(
    collections.namedtuple(
        'SwapInfo',
        [
            'total',
            'free',
            'used',
            'sin',
            'sout'
        ]
    )
):
    """
    get_swapinfo will return a SWAPINFO
    """


def get_swapinfo():
    """
    get swamp info of the system
    """
    decorators.needlinux(True)
    fp = open('/proc/swaps', 'r')
    reg = '([\\/A-Za-z0-9]+)[\\s]+([a-z]+)[\\s]+([0-9]+)'\
        '[\\s]+([0-9]+)[\\s]+([\\-0-9]+).*'
    regobj = re.compile(reg)
    total = used = 0
    try:
        for line in fp:
            if regobj.search(line) is not None:
                sp = line.split()
                total += int(sp[2])
                used += int(sp[3])
    finally:
        fp.close()

    if total == 0:
        total = used = 0
        msg = 'Failed to get total from /proc/swaps or '\
            'the system does not have swap mounted.' \
            ' Total and used were set to 0'
        warnings.warn(msg, RuntimeWarning)

    sin = sout = None
    fp = open('/proc/vmstat', 'r')
    try:
        for line in fp:
            # values are expressed in 4 kilo bytes, we want bytes instead
            if line.startswith('pswpin'):
                sin = int(line.split(' ')[1]) * 4 * 1024
            elif line.startswith('pswpout'):
                sout = int(line.split(' ')[1]) * 4 * 1024
            if sin is not None and sout is not None:
                break
        else:
            # we might get here when dealing with exotic Linux flavors, see:
            # http://code.google.com/p/psutil/issues/detail?id=313
            msg = "'sin' and 'sout' swap memory stats couldn't " \
                  "be determined and were set to 0"
            warnings.warn(msg, RuntimeWarning)
            sin = sout = 0
    finally:
        fp.close()
    free = total - used

    return SWAPINFO(total, free, used, sin, sout)


def net_io_counters():
    """
    get network statistics with a list of namedtuple
    (bytes_sent, bytes_recv, packets_sent, packets_recv,
                         errin, errout, dropin, dropout)
    example
    ::
       {
           'lo':
            (
                235805206817, 235805206817, 315060887, 315060887, 0, 0, 0, 0
            ),
            'eth1':
            (
                18508976300272, 8079464483699, 32776530804,
                32719666038, 0, 0, 708015, 0
            ),
            'eth0':
            (
                0, 0, 0, 0, 0, 0, 0, 0
            )
        }
    """
    decorators.needlinux(True)
    fhandle = open("/proc/net/dev", "r")
    try:
        lines = fhandle.readlines()
    finally:
        fhandle.close()
    retdict = {}
    for line in lines[2:]:
        colon = line.rfind(':')
        assert colon > 0, repr(line)
        name = line[:colon].strip()
        fields = line[colon + 1:].strip().split()
        bytes_recv = int(fields[0])
        packets_recv = int(fields[1])
        errin = int(fields[2])
        dropin = int(fields[3])
        bytes_sent = int(fields[8])
        packets_sent = int(fields[9])
        errout = int(fields[10])
        dropout = int(fields[11])
        retdict[name] = (bytes_sent, bytes_recv, packets_sent, packets_recv,
                         errin, errout, dropin, dropout)
    return retdict


def get_net_through(str_interface):
    """
    get network interface statistics by a interface (eth0, e,g,)
    """
    decorators.needlinux(True)
    rx_bytes = tx_bytes = -1
    fp = open('/proc/net/dev', 'r')
    try:
        for line in fp:
            if str_interface in line:
                data = line.split('%s:' % str_interface)[1].split()
                rx_bytes, tx_bytes = (data[0], data[8])
    finally:
        fp.close()
    if rx_bytes < 0 or tx_bytes < 0:
        msg = 'Failed to parse /proc/net/dev'
        warnings.warn(msg, RuntimeWarning)
    cup.unittest.assert_ge(rx_bytes, 0)
    cup.unittest.assert_ge(tx_bytes, 0)
    return (int(rx_bytes), int(tx_bytes))


def get_net_transmit_speed(str_interface, intvl_in_sec=1):
    """
    get network interface write/read speed

    E.g.
    ::
        import cup
        print cup.res.linux.get_net_transmit_speed('eth1', 5)

    """
    decorators.needlinux(True)
    cup.unittest.assert_gt(intvl_in_sec, 0)
    rx_bytes0 = get_net_through(str_interface)[0]
    time.sleep(intvl_in_sec)
    rx_bytes1 = get_net_through(str_interface)[0]
    return (rx_bytes1 - rx_bytes0) / intvl_in_sec



def get_net_recv_speed(str_interface, intvl_in_sec):
    """
    get average network recv-speed during a time period (intvl_in_sec)
    """
    decorators.needlinux(True)
    cup.unittest.assert_gt(intvl_in_sec, 0)
    tx_bytes0 = get_net_through(str_interface)[1]
    time.sleep(intvl_in_sec)
    tx_bytes1 = get_net_through(str_interface)[1]
    return (tx_bytes1 - tx_bytes0) / intvl_in_sec


def wrap_exceptions(fun):
    """
    Decorator which translates bare OSError and IOError exceptions
    into cup.err.NoSuchProcess and cup.err.AccessDenied.
    """
    @wraps(fun)
    def wrapper(self, *args, **kwargs):
        """
        internal wrapper for wrap_exceptions
        """
        try:
            return fun(self, *args, **kwargs)
        except EnvironmentError as error:
            # ENOENT (no such file or directory) gets raised on open().
            # ESRCH (no such process) can get raised on read() if
            # process is gone in meantime.
            err = sys.exc_info()[1]
            if err.errno in (errno.ENOENT, errno.ESRCH):
                # pylint: disable=W0212
                raise cup.err.NoSuchProcess(self._pid, self._process_name)
            if err.errno in (errno.EPERM, errno.EACCES):
                raise cup.err.ResException('EPERM or EACCES')
            raise error
    return wrapper


CLOCK_TICKS = os.sysconf("SC_CLK_TCK")
def boot_time():
    """Return the system boot time expressed in seconds since the epoch.
    """
    decorators.needlinux(True)
    with open('/proc/stat', 'rb') as f:
        for line in f:
            if line.startswith(b'btime'):
                ret = float(line.strip().split()[1])
                return ret
        raise RuntimeError("line 'btime' not found in /proc/stat")


def pids():
    """Returns a list of PIDs currently running on the system."""
    decorators.needlinux(True)
    return [int(x) for x in os.listdir(b'/proc') if x.isdigit()]

_pmap = {}


def process_iter():
    """Return a generator yielding a Process instance for all
    running processes.

    Every new Process instance is only created once and then cached
    into an internal table which is updated every time this is used.

    Cached Process instances are checked for identity so that you're
    safe in case a PID has been reused by another process, in which
    case the cached instance is updated.

    yuetian:
    1. the origion use a check_running function to check whether
    PID has been reused by another process in which case yield a new
    Process instance
    hint:i did not use check_running function because the container of
    pid is set

    2. the origion use a sorted list(_pmap.items()) +
        list(dict.fromkeys(new_pids).items()
    to get pid and proc to make res.proc is only a instance of a pid Process
    hint(bugs):i did not use fromkeys(new_pids) because i did not get the meanning
    of using proc
    """
    decorators.needlinux(True)
    pid_set = set(pids())
    for pid in pid_set:
        try:
            check_process = Process(pid)
            res = check_process.get_process_name()
        except cup.err.NoSuchProcess:
            pass
        else:
            yield check_process


# pylint: disable=R0904
class Process(object):
    """
    Process info query (given a pid)
    """

    __slots__ = ["_pid", "_process_name", "_create_time"]

    def __init__(self, pid):
        decorators.needlinux(True)
        self._pid = pid
        self._process_name = None
        self._create_time = None
        if not os.path.lexists("/proc/%s/exe" % self._pid):
            raise cup.err.NoSuchProcess(self._pid, self._process_name)
        else:
            self._create_time = self.create_time()

    def create_time(self):
        """return -1 represent the process does not exists
        """
        #if not os.path.lexists("/proc/%s/exe" % self._pid):
        #    raise cup.err.NoSuchProcess(self._pid, self._process_name)
        #else:
        try:
            with open("/proc/%s/stat" % self._pid, 'rb') as f:
                st = f.read().strip()
        except IOError:
            return -1
        else:
            st = st[st.rfind(b')') + 2:]
            st = st[st.rfind(b')') + 2:]
            values = st.split(b' ')
            bt = boot_time()
            return (float(values[19]) / CLOCK_TICKS) + bt

    def children(self, recursive=False):
        """Return the children of this process as a list of Process
        instances, pre-emptively checking whether PID has been reused.
        If recursive is True return all the parent descendants.

        Example (A == this process):

         A ─┐
            │
            ├─ B (child) ─┐
            │             └─ X (grandchild) ─┐
            │                                └─ Y (great grandchild)
            ├─ C (child)
            └─ D (child)
        """
        ppid_map = None
        ret = []
        if not recursive:
            # 'slow' version, common to all platforms except Windows
            for p in process_iter():
                #try:
                if p.get_process_ppid() == self._pid:
                    # if child happens to be older than its parent
                    # (self) it means child's PID has been reused
                    if self.create_time() <= p.create_time():
                        ret.append(p._pid)
                #except (cup.err.NoSuchProcess):
                #    pass
        else:
            # construct a dict where 'values' are all the processes
            # having 'key' as their parent
            table = collections.defaultdict(list)
            for p in process_iter():
                try:
                    table[p.get_process_ppid()].append(p)
                except (cup.err.NoSuchProcess):
                    pass
            # At this point we have a mapping table where table[self.pid]
            # are the current process' children.
            # Below, we look for all descendants recursively, similarly
            # to a recursive function call.
            checkpids = [self._pid]
            for pid in checkpids:
                for child in table[pid]:
                    try:
                        # if child happens to be older than its parent
                        # (self) it means child's PID has been reused
                        intime = self.create_time() <= child.create_time()
                    except (cup.err.NoSuchProcess):
                        pass
                    else:
                        if intime:
                            ret.append(child._pid)
                            if child._pid not in checkpids:
                                checkpids.append(child._pid)
        return ret

    @wrap_exceptions
    def get_process_name(self):
        """
        get process name of the process (for daemon process only)
        """
        fhandle = open("/proc/%s/stat" % self._pid)
        try:
            name = fhandle.read().split(' ')[1].replace('(', '').replace(
                ')', ''
            )
        finally:
            fhandle.close()
        return name

    def get_process_exe(self):
        """
        get executable info of the process. If the process is a daemon, use
        get_process_name instead!
        """
        try:
            exe = os.readlink("/proc/%s/exe" % self._pid)
        except (OSError, IOError) as error:
            err = sys.exc_info()[1]
            if err.errno == errno.ENOENT:
                # no such file error; might be raised also if the
                # path actually exists for system processes with
                # low pids (about 0-20)
                if os.path.lexists("/proc/%s/exe" % self._pid):
                    return ""
                else:
                    # ok, it is a process which has gone away
                    raise cup.err.NoSuchProcess(self._pid, self._process_name)
            if err.errno in (errno.EPERM, errno.EACCES):
                raise cup.err.AccessDenied(self._pid, self._process_name)
            raise error

        # readlink() might return paths containing null bytes causing
        # problems when used with other fs-related functions (os.*,
        # open(), ...)
        exe = exe.replace('\x00', '')
        # Certain names have ' (deleted)' appended. Usually this is
        # bogus as the file actually exists. Either way that's not
        # important as we don't want to discriminate executables which
        # have been deleted.
        if exe.endswith(" (deleted)") and not os.path.exists(exe):
            exe = exe[:-10]
        return exe

    @wrap_exceptions
    def get_process_cmdline(self):
        """
        get cmdline
        """
        fhandle = open("/proc/%s/cmdline" % self._pid)
        try:
            # return the args as a list
            return [x for x in fhandle.read().split('\x00') if x]
        finally:
            fhandle.close()

    __nt_io = collections.namedtuple(
        'nt_io',
        [
            'rcount',
            'wcount',
            'rbytes',
            'wbytes'
        ]
    )

    @wrap_exceptions
    def get_process_io_counters(self):
        """
        get io statistics info of network adapters.
        """
        if not os.path.exists('/proc/%s/io' % os.getpid()):
            raise NotImplementedError("couldn't find /proc/%s/io (kernel "
                                      "too old?)" % self._pid)
        fname = "/proc/%s/io" % self._pid
        # pylint: disable=c0103
        f = open(fname)
        try:
            rcount = wcount = rbytes = wbytes = None
            for line in f:
                if rcount is None and line.startswith("syscr"):
                    rcount = int(line.split()[1])
                elif wcount is None and line.startswith("syscw"):
                    wcount = int(line.split()[1])
                elif rbytes is None and line.startswith("read_bytes"):
                    rbytes = int(line.split()[1])
                elif wbytes is None and line.startswith("write_bytes"):
                    wbytes = int(line.split()[1])
            for _ in (rcount, wcount, rbytes, wbytes):
                if _ is None:
                    raise NotImplementedError(
                        "couldn't read all necessary info from %r" % fname)
            return self.__nt_io(rcount, wcount, rbytes, wbytes)
        finally:
            f.close()

    _nt_cputimes = collections.namedtuple(
        'nt_cputimes',
        [
            'utime',
            'stime'
        ]
    )

    @wrap_exceptions
    def get_cpu_times(self):
        """
        get cpu times, return with a namedtuple (utime, stime)
        """
        f = open("/proc/%s/stat" % self._pid)
        try:
            st = f.read().strip()
        finally:
            f.close()
        # ignore the first two values ("pid (exe)")
        st = st[st.find(')') + 2:]
        values = st.split(' ')
        utime = float(values[11]) / _CLOCK_TICKS
        stime = float(values[12]) / _CLOCK_TICKS
        return self._nt_cputimes(utime, stime)

    @wrap_exceptions
    def get_cpu_usage(self, interval=0.5):
        """get cpu usage"""
        now = self.get_cpu_times()
        time.sleep(interval)
        then = self.get_cpu_times()
        return float(
            (then[0] - now[0] + then[1] - now[1]) * 100 / interval
        )

    @wrap_exceptions
    def get_process_create_time(self):
        """
        get process create time
        """
        f = open("/proc/%s/stat" % self._pid)
        try:
            st = f.read().strip()
        finally:
            f.close()
        # ignore the first two values ("pid (exe)")
        st = st[st.rfind(')') + 2:]
        values = st.split(' ')
        # According to documentation, starttime is in field 21 and the
        # unit is jiffies (clock ticks).
        # We first divide it for clock ticks and then add uptime returning
        # seconds since the epoch, in UTC.
        starttime = (float(values[19]) / _CLOCK_TICKS) + \
            get_boottime_since_epoch()
        return starttime

    _nt_meminfo = collections.namedtuple(
        'nt_meminfo',
        [
            'rss',
            'vms'
        ]
    )

    @wrap_exceptions
    def get_memory_info(self):
        """
        get memory info, return with a namedtuple (
        rss vms shared text lib data dirty)
        """
        f = open("/proc/%s/statm" % self._pid)
        try:
            vms, rss = f.readline().split()[:2]
            return self._nt_meminfo(
                int(rss) * _PAGESIZE,
                int(vms) * _PAGESIZE
            )
        finally:
            f.close()

    _nt_ext_mem = collections.namedtuple(
        'meminfo',
        'rss vms shared text lib data dirty'
    )

    @wrap_exceptions
    def get_ext_memory_info(self):
        """
        return namedtuple with FIELDs below:

        Example: ::

            from cup.res import linux
            process = linux.Process(pid)
            print process.rss, process.dirty

        +--------+-------------------------------------+------+------+
        | FIELD  | DESCRIPTION                         | AKA  | TOP  |
        +========+=====================================+======+======+
        | rss    | resident set size                   |  /   | RES  |
        +--------+-------------------------------------+------+------+
        | vms    | total program size                  | size | VIRT |
        +--------+-------------------------------------+------+------+
        | shared | shared pages (from shared mappings) |  /   | SHR  |
        +--------+-------------------------------------+------+------+
        | text   | text ('code')                       | trs  | CODE |
        +--------+-------------------------------------+------+------+
        | lib    | library (unused in Linux 2.6)       | lrs  |   /  |
        +--------+-------------------------------------+------+------+
        | data   | data + stack                        | drs  | DATA |
        +--------+-------------------------------------+------+------+
        | dirty  | dirty pages (unused in Linux 2.6)   | dt   |   /  |
        +--------+-------------------------------------+------+------+
        """
        f = open("/proc/%s/statm" % self._pid)
        try:
            vms, rss, shared, text, lib, data, dirty = \
                [int(x) * _PAGESIZE for x in f.readline().split()[:7]]
        finally:
            f.close()
        return self._nt_ext_mem(rss, vms, shared, text, lib, data, dirty)

    _mmap_base_fields = ['path', 'rss', 'size', 'pss', 'shared_clean',
                         'shared_dirty', 'private_clean', 'private_dirty',
                         'referenced', 'anonymous', 'swap', ]
    nt_mmap_grouped = collections.namedtuple(
        'mmap', ' '.join(_mmap_base_fields)
    )
    nt_mmap_ext = collections.namedtuple(
        'mmap', 'addr perms ' + ' '.join(_mmap_base_fields)
    )

    def get_memory_maps(self):
        """
        get memory map (from /proc smaps file)
        """
        # Return process's mapped memory regions as a list of nameduples.
        # Fields are explained in 'man proc'; here is an updated (Apr 2012)
        # version: http://goo.gl/fmebo

        if not os.path.exists('/proc/%s/smaps' % os.getpid()):
            msg = "couldn't find /proc/%s/smaps; kernel < 2.6.14 or CONFIG_MMU " \
                  "kernel configuration option is not enabled" % self._pid
            raise NotImplementedError(msg)

        f = None
        try:
            f = open("/proc/%s/smaps" % self._pid)
            first_line = f.readline()
            current_block = [first_line]

            def get_blocks():
                """
                internal get blocks  for get_memory_maps
                """
                data = {}
                for line in f:
                    fields = line.split(None, 5)
                    if not fields[0].endswith(':'):
                        # new block section
                        yield (current_block.pop(), data)
                        current_block.append(line)
                    else:
                        try:
                            data[fields[0]] = int(fields[1]) * 1024
                        except ValueError:
                            if fields[0].startswith('VmFlags:'):
                                # see issue # 369
                                continue
                            else:
                                raise ValueError("don't know how to interpret"
                                                 " line %r" % line)
                yield (current_block.pop(), data)

            if first_line:  # smaps file can be empty
                for header, data in get_blocks():
                    hfields = header.split(None, 5)
                    try:
                        addr, perms, offset, dev, inode, path = hfields
                    except ValueError:
                        addr, perms, offset, dev, inode, path = hfields + ['']
                    if not path:
                        path = '[anon]'
                    else:
                        path = path.strip()
                    yield (addr, perms, path,
                           data['Rss:'],
                           data.get('Size:', 0),
                           data.get('Pss:', 0),
                           data.get('Shared_Clean:', 0),
                           data.get('Shared_Dirty:', 0),
                           data.get('Private_Clean:', 0),
                           data.get('Private_Dirty:', 0),
                           data.get('Referenced:', 0),
                           data.get('Anonymous:', 0),
                           data.get('Swap:', 0))
            f.close()
        except EnvironmentError as error:
            # XXX - Can't use wrap_exceptions decorator as we're
            # returning a generator;  this probably needs some
            # refactoring in order to avoid this code duplication.
            if f is not None:
                f.close()
            err = sys.exc_info()[1]
            if err.errno in (errno.ENOENT, errno.ESRCH):
                raise cup.err.NoSuchProcess(self._pid, self._process_name)
            if err.errno in (errno.EPERM, errno.EACCES):
                raise cup.err.AccessDenied(self._pid, self._process_name)
            raise error
        except Exception as error:
            if f is not None:
                f.close()
            raise error
        f.close()

    @wrap_exceptions
    def get_process_cwd(self):
        """
        get process current working direcotry
        """
        path = os.readlink("/proc/%s/cwd" % self._pid)
        return path.replace('\x00', '')

    _nt_ctxsw = collections.namedtuple(
        'voluntary_ctxt_switches',
        [
            'vol',
            'unvol'
        ]
    )
    @wrap_exceptions
    def get_num_ctx_switches(self):
        """
        get process context switch info (from /proc status file), return
        with a namedtuple (vol, unvol)
        """
        vol = unvol = None
        f = open("/proc/%s/status" % self._pid)
        try:
            for line in f:
                if line.startswith("voluntary_ctxt_switches"):
                    vol = int(line.split()[1])
                elif line.startswith("nonvoluntary_ctxt_switches"):
                    unvol = int(line.split()[1])
                if vol is not None and unvol is not None:
                    return self._nt_ctxsw(vol, unvol)
            raise NotImplementedError(
                "'voluntary_ctxt_switches' and 'nonvoluntary_ctxt_switches'"
                "fields were not found in /proc/%s/status; the kernel is "
                "probably older than 2.6.23" % self._pid)
        finally:
            f.close()

    @wrap_exceptions
    def get_process_num_threads(self):
        """
        get threads num of this process
        """
        f = open("/proc/%s/status" % self._pid)
        try:
            for line in f:
                if line.startswith("Threads:"):
                    return int(line.split()[1])
            raise NotImplementedError("line not found")
        finally:
            f.close()

    _thread_tuple = collections.namedtuple(
        'ntuple',
        [
            'thread_id',
            'utime',
            'stime'
        ]
    )

    @wrap_exceptions
    def get_process_threads(self):
        """
        get threads that is current using, return with a namedtuple (
        thread_id, utime, stime)
        """
        thread_ids = os.listdir("/proc/%s/task" % self._pid)
        thread_ids.sort()
        retlist = []
        hit_enoent = False
        for thread_id in thread_ids:
            try:
                f = open("/proc/%s/task/%s/stat" % (self._pid, thread_id))
            except EnvironmentError as error:
                err = sys.exc_info()[1]
                if err.errno == errno.ENOENT:
                    # no such file or directory; it means thread
                    # disappeared on us
                    hit_enoent = True
                    continue
                raise error
            try:
                st = f.read().strip()
            finally:
                f.close()
            # ignore the first two values ("pid (exe)")
            st = st[st.find(')') + 2:]
            values = st.split(' ')
            utime = float(values[11]) / _CLOCK_TICKS
            stime = float(values[12]) / _CLOCK_TICKS
            ntuple = self._thread_tuple(int(thread_id), utime, stime)
            retlist.append(ntuple)
        if hit_enoent:
            # raise NSP if the process disappeared on us
            os.stat('/proc/%s' % self._pid)
        return retlist

    @wrap_exceptions
    def get_process_nice(self):
        """
        get process nice
        """
        f = open('/proc/%s/stat' % self._pid, 'r')
        try:
            data = f.read()
            return int(data.split()[18])
        finally:
            f.close()

    @wrap_exceptions
    def get_process_status(self):
        """
        get status of the current process (info from /proc/xxx/status)
        """
        f = open("/proc/%s/status" % self._pid)
        try:
            for line in f:
                if line.startswith("State:"):
                    letter = line.split()[1]
                    # XXX is '?' legit? (we're not supposed to return
                    # it anyway)
                    return _PROC_STATUSES.get(letter, '?')
        finally:
            f.close()

    _nt_openfile = collections.namedtuple(
        'nt_openfile',
        [
            'file',
            'fd'
        ]
    )

    @wrap_exceptions
    def get_open_files(self):
        """
        get opened file info
        """
        retlist = []
        files = os.listdir("/proc/%s/fd" % self._pid)
        hit_enoent = False
        for fd in files:
            file = "/proc/%s/fd/%s" % (self._pid, fd)
            if os.path.islink(file):
                try:
                    file = os.readlink(file)
                except OSError as error:
                    # ENOENT == file which is gone in the meantime
                    err = sys.exc_info()[1]
                    if err.errno == errno.ENOENT:
                        hit_enoent = True
                        continue
                    raise error
                else:
                    # If file is not an absolute path there's no way
                    # to tell whether it's a regular file or not,
                    # so we skip it. A regular file is always supposed
                    # to be absolutized though.
                    if file.startswith('/') and os.path.isfile(file):
                        ntuple = self._nt_openfile(file, int(fd))
                        retlist.append(ntuple)
        if hit_enoent:
            # raise NSP if the process disappeared on us
            os.stat('/proc/%s' % self._pid)
        return retlist

    _nt_connection = collections.namedtuple(
        'nt_connection',
        [
            'fd',
            'family',
            'type',
            'laddr',
            'raddr',
            'status'
        ]
    )

    def _process_for_connections(self, inodes, file, family, type_):
        retlist = []
        try:
            f = open(file, 'r')
        except IOError as error:
            # IPv6 not supported on this platform
            err = sys.exc_info()[1]
            if err.errno == errno.ENOENT and file.endswith('6'):
                return []
            else:
                raise error
        try:
            f.readline()  # skip the first line
            for line in f:
                # IPv4 / IPv6
                if family in (socket.AF_INET, socket.AF_INET6):
                    _, laddr, raddr, status, _, _, _, _, _, inode = \
                        line.split()[:10]
                    if inode in inodes:
                        laddr = self._decode_address(laddr, family)
                        raddr = self._decode_address(raddr, family)
                        if type_ == socket.SOCK_STREAM:
                            status = _TCP_STATUSES[status]
                        else:
                            status = _CONN_NONE
                        fd = int(inodes[inode])
                        conn = self._nt_connection(
                            fd, family, type_, laddr,
                            raddr, status
                        )
                        retlist.append(conn)
                elif family == socket.AF_UNIX:
                    tokens = line.split()
                    _, _, _, _, type_, _, inode = tokens[0:7]
                    if inode in inodes:

                        if len(tokens) == 8:
                            path = tokens[-1]
                        else:
                            path = ""
                        fd = int(inodes[inode])
                        type_ = int(type_)
                        conn = self._nt_connection(
                            fd, family, type_, path,
                            None, _CONN_NONE
                        )
                        retlist.append(conn)
                else:
                    raise ValueError(family)
            return retlist
        finally:
            f.close()

    @wrap_exceptions
    def get_connections(self, kind='inet'):
        """
        get network connection info, each item contains a namedtuple
        (fd family type laddr raddr status)

        :param kind:
            kind='inet' by default
        :return:
            a list of network connection info
        """

        # Return connections opened by process as a list of namedtuples.
        # The kind parameter filters for connections that fit the following
        # criteria:

        # Kind Value      Number of connections using
        # inet            IPv4 and IPv6
        # inet4           IPv4
        # inet6           IPv6
        # tcp             TCP
        # tcp4            TCP over IPv4
        # tcp6            TCP over IPv6
        # udp             UDP
        # udp4            UDP over IPv4
        # udp6            UDP over IPv6
        # all             the sum of all the possible families and protocols
        # Note: in case of UNIX sockets we're only able to determine the
        # local bound path while the remote endpoint is not retrievable:
        # http://goo.gl/R3GHM
        inodes = {}
        # os.listdir() is gonna raise a lot of access denied
        # exceptions in case of unprivileged user; that's fine:
        # lsof does the same so it's unlikely that we can to better.
        for fd in os.listdir("/proc/%s/fd" % self._pid):
            try:
                inode = os.readlink("/proc/%s/fd/%s" % (self._pid, fd))
            except OSError:
                continue
            if inode.startswith('socket:['):
                # the process is using a socket
                inode = inode[8:][:-1]
                inodes[inode] = fd

        if not inodes:
            # no connections for this process
            return []

        tcp4 = ("tcp", socket.AF_INET, socket.SOCK_STREAM)
        tcp6 = ("tcp6", socket.AF_INET6, socket.SOCK_STREAM)
        udp4 = ("udp", socket.AF_INET, socket.SOCK_DGRAM)
        udp6 = ("udp6", socket.AF_INET6, socket.SOCK_DGRAM)
        unix = ("unix", socket.AF_UNIX, None)

        tmap = {
            "all": (tcp4, tcp6, udp4, udp6, unix),
            "tcp": (tcp4, tcp6),
            "tcp4": (tcp4, ),
            "tcp6": (tcp6, ),
            "udp": (udp4, udp6),
            "udp4": (udp4, ),
            "udp6": (udp6, ),
            "unix": (unix, ),
            "inet": (tcp4, tcp6, udp4, udp6),
            "inet4": (tcp4, udp4),
            "inet6": (tcp6, udp6),
        }
        if kind not in tmap:
            raise ValueError("invalid %r kind argument; choose between %s"
                             % (kind, ', '.join([repr(x) for x in tmap])))
        ret = []
        for f, family, type_ in tmap[kind]:
            ret += self._process_for_connections(
                inodes, "/proc/net/%s" % f, family, type_
            )
        # raise NSP if the process disappeared on us
        os.stat('/proc/%s' % self._pid)
        return ret

    @wrap_exceptions
    def get_num_fds(self):
        """
        get opened file descriptor num
        """
        return len(os.listdir("/proc/%s/fd" % self._pid))

    @wrap_exceptions
    def get_process_ppid(self):
        """
        get parent process id
        """
        f = open("/proc/%s/status" % self._pid)
        try:
            for line in f:
                if line.startswith("PPid:"):
                    # PPid: nnnn
                    return int(line.split()[1])
            raise NotImplementedError("line not found")
        finally:
            f.close()

    _nt_uids = collections.namedtuple(
        'nt_uids',
        [
            'real',
            'effective',
            'saved'
        ]
    )

    @wrap_exceptions
    def get_process_uids(self):
        """
        get uid info of the process, will return a namedtuple
        """
        f = open("/proc/%s/status" % self._pid)
        try:
            for line in f:
                if line.startswith('Uid:'):
                    _, real, effective, saved, fs = line.split()
                    return self._nt_uids(int(real), int(effective), int(saved))
            raise NotImplementedError("line not found")
        finally:
            f.close()

    _nt_gids = collections.namedtuple(
        'nt_gids',
        [
            'real',
            'effective',
            'saved'
        ]
    )

    @wrap_exceptions
    def get_process_gids(self):
        """
        get process gid, namedtuple will be returned
        (with attrs .real .effective .saved)
        """
        f = open("/proc/%s/status" % self._pid)
        try:
            for line in f:
                if line.startswith('Gid:'):
                    _, real, effective, saved, fs = line.split()
                    return self._nt_gids(int(real), int(effective), int(saved))
            raise NotImplementedError("line not found")
        finally:
            f.close()

    @staticmethod
    def _decode_address(addr, family):
        """Accept an "ip:port" address as displayed in /proc/net/*
        and convert it into a human readable form, like:

        "0500000A:0016" -> ("10.0.0.5", 22)
        "0000000000000000FFFF00000100007F:9E49" -> ("::ffff:127.0.0.1", 40521)

        The IP address portion is a little or big endian four-byte
        hexadecimal number; that is, the least significant byte is listed
        first, so we need to reverse the order of the bytes to convert it
        to an IP address.
        The port is represented as a two-byte hexadecimal number.

        Reference:
        http://linuxdevcenter.com/pub/a/linux/2000/11/16/LinuxAdmin.html
        """
        ip, port = addr.split(':')
        port = int(port, 16)
        if sys.version_info >= (3, 0):
            ip = ip.encode('ascii')
        # this usually refers to a local socket in listen mode with
        # no end-points connected
        if not port:
            return ()
        if family == socket.AF_INET:
            # see: http://code.google.com/p/psutil/issues/detail?id=201
            if sys.byteorder == 'little':
                ip = socket.inet_ntop(family, base64.b16decode(ip)[::-1])
            else:
                ip = socket.inet_ntop(family, base64.b16decode(ip))
        else:  # IPv6
            # old version - let's keep it, just in case...
            # ip = ip.decode('hex')
            # return socket.inet_ntop(socket.AF_INET6,
            #          ''.join(ip[i:i+4][::-1] for i in range(0, 16, 4)))
            ip = base64.b16decode(ip)
            # see: http://code.google.com/p/psutil/issues/detail?id=201
            if sys.byteorder == 'little':
                ip = socket.inet_ntop(
                    socket.AF_INET6,
                    struct.pack('>4I', *struct.unpack('<4I', ip)))
            else:
                ip = socket.inet_ntop(
                    socket.AF_INET6,
                    struct.pack('<4I', *struct.unpack('<4I', ip)))
        return (ip, port)

    def getpgid(self):
        """
        return process group id (not pid, not gid either)
        """
        return os.getpgid(self._pid)


if '__main__' == __name__:
    # system info
    print(get_boottime_since_epoch())
    print(get_cpu_nums())
    print(get_kernel_version())
    print(get_disk_usage_all())
    print(get_disk_info())

    # resouce info
    print(get_cpu_usage(2))
    print(get_cpu_core_usage(0, 0.5))
    print(get_meminfo())
    print(get_swapinfo())
    print(get_net_through('xgbe0'))
    print(get_net_transmit_speed('xgbe0', 5))
    print(get_net_recv_speed('xgbe0', 5))
    print(net_io_counters())

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
