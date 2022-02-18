#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    pollers for epoll and kqueue and others.
    Refer IOLoop from tornado:
        https://www.tornadoweb.org/en/branch2.0/_modules/tornado/ioloop.html
    Respect to the tornado team:

Tornado is based on Apache V2.0 License. Here it goes:

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""
import abc
import select

from cup import log
from cup import const
from cup import platforms


IONEW = 0x0
EPOLLIN = 0x001
EPOLLPRI = 0x002
EPOLLOUT = 0x004
EPOLLERR = 0x008
EPOLLHUP = 0x010
EPOLLRDHUP = 0x2000


WRITE = EPOLLOUT
READ = EPOLLIN
ERROR = EPOLLERR | EPOLLHUP | EPOLLRDHUP


class BasePoller(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def fileno(self):
        """
        return fileno of the poller
        """

    @abc.abstractmethod
    def register(self, fd, events):
        """
        register fd
        """

    @abc.abstractmethod
    def unregister(self, fd):
        """
        unregister fd
        """

    @abc.abstractmethod
    def modify(self, fd, events):
        """
        modify fd to newmode
        """

    @abc.abstractmethod
    def poll(self, wait_time):
        """
        poll until wait_times passes.
        """


class Epoller(BasePoller):
    """
    epoll for linux and others
    """
    def __init__(self):
        """
        """
        self._epoll = select.epoll()

    def write_params(self):
        """epoll write params"""
        return (select.EPOLLET | select.EPOLLOUT | select.EPOLLERR)

    def read_params(self):
        """epoll read params"""
        return (select.EPOLLET | select.EPOLLIN | select.EPOLLERR)

    def fileno(self):
        """return fileno of epoll object"""
        return self._epoll.fileno()

    def register(self, fd, events):
        """
        register events for a fd
        """
        events = events | select.EPOLLET | select.EPOLLERR
        self._epoll.register(fd, events)

    def unregister(self, fd):
        """
        unregister for epoll
        """
        self._epoll.unregister(fd)

    def modify(self, fd, events):
        """modify kqueue events"""
        self._epoll.modify(fd, events)

    def poll(self, wait_time):
        """start to poll"""
        return self._epoll.poll(wait_time)


class KQueuePoller(BasePoller):
    """
    kqueue for macos
    """
    def __init__(self):
        """
        """
        self._kq = select.kqueue()

    def fileno(self):
        """return fileno of kqueue object"""
        return self._kq.fileno()

    def register(self, fd, events):
        """
        register events for a fd
        """
        # NOTE: KQ_EV_CLEAR should be set as
        # it means edge trigger like EPOLLET
        self.kvent_control(fd, events, select.KQ_EV_ADD | select.KQ_EV_CLEAR)

    def unregister(self, fd):
        """
        unregister for kevents
        """
        events = READ | WRITE
        self.kvent_control(fd, events, select.KQ_EV_DELETE)

    def modify(self, fd, events):
        """modify kqueue events"""
        self.unregister(fd)
        self.register(fd, events)

    def kvent_control(self, fd, events, flags):
        """kevent control"""
        kevents = []
        if events & WRITE:
            kevents.append(select.kevent(
                    fd, filter=select.KQ_FILTER_WRITE, flags=flags))
        if events & READ or not kevents:
            kevents.append(select.kevent(
                    fd, filter=select.KQ_FILTER_READ, flags=flags))
        for kevent in kevents:
            self._kq.control([kevent], 0)

    def poll(self, wait_time):
        """kqueue poll"""
        kevts = self._kq.control(None, 1000, wait_time)
        events = {}
        for kevent in kevts:
            fd = kevent.ident
            if kevent.filter == select.KQ_FILTER_READ:
                events[fd] = events.get(fd, 0) | READ
            if kevent.filter == select.KQ_FILTER_WRITE:
                if kevent.flags & select.KQ_EV_EOF:
                    # if KQ_EV_EOF received, it means the peer has closed
                    # / refused the socket
                    events[fd] = ERROR
                else:
                    events[fd] = events.get(fd, 0) | WRITE
            if kevent.flags & select.KQ_EV_ERROR:
                events[fd] = events.get(fd, 0) | ERROR
        return events.items()


class SelectPoller(BasePoller):
    """ downgraded to select.select()"""
    def __init__(self):
        """not epoll and not kqueue, downgraded to select.select"""
        self._read_fds = []
        self._write_fds = []
        self._error_fds = []

    def register(self, fd, events):
        if events & READ:
            self.read_fds.add(fd)
        if events & WRITE:
            self.write_fds.add(fd)
        if events & ERROR:
            self.error_fds.add(fd)
            # Closed connections are reported as errors by epoll and kqueue,
            # but as zero-byte reads by select, so when errors are requested
            # we need to listen for both read and error.
            self.read_fds.add(fd)

    def modify(self, fd, events):
        self.unregister(fd)
        self.register(fd, events)

    def unregister(self, fd):
        self.read_fds.discard(fd)
        self.write_fds.discard(fd)
        self.error_fds.discard(fd)

    def poll(self, timeout):
        readable, writeable, errors = select.select(
            self.read_fds, self.write_fds, self.error_fds, timeout
        )
        events = {}
        for fd in readable:
            events[fd] = events.get(fd, 0) | READ
        for fd in writeable:
            events[fd] = events.get(fd, 0) | WRITE
        for fd in errors:
            events[fd] = events.get(fd, 0) | ERROR
        return events.items()


class PollerFactory(object):
    """Poller Factory"""

    def __init__(self):
        """
        """
        self._polldict = []
        self._poller = None
        self._started = False
        if hasattr(select, 'epoll'):
            self._poller = Epoller()
        elif hasattr(select, 'kqueue'):
            self._poller = KQueuePoller()
        else:
            self._poller = SelectPoller()

    def stop(self):
        """stop the poller factory"""
        self._started = False

    def register(self, fd, events):
        """
        register
        """
        self._poller.register(fd, events)

    def modify(self, fd, events):
        self._poller.modify(fd, events)

    def unregister(self, fd):
        """unregister"""
        self._poller.unregister(fd)

    def poll(self, wait_time):
        """poll"""
        self._started = True
        return self._poller.poll(wait_time)


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
