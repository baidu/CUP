#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    1. Delay-execute sth after several seconds

    2. Schedule some tasks in a queue.
"""

try:
    # pylint:disable=F0401
    import queue
except ImportError:
    import Queue as queue
import threading
import traceback

from cup.util import threadpool
from cup import log

URGENCY_HIGH = 0
URGENCY_NORMAL = 1
URGENCY_LOW = 2

class ExecutionService(object):
    """
    execution service
    """
    def __init__(
        self, delay_exe_thdnum=3, queue_exec_thdnum=4, name=None
    ):
        self.__toal_thdnum = delay_exe_thdnum + queue_exec_thdnum
        self.__delay_exe_thdnum = delay_exe_thdnum
        self.__queue_exe_thdnum = queue_exec_thdnum
        self.__delay_queue = queue.PriorityQueue()
        self.__exec_queue = queue.PriorityQueue()
        self.__thdpool = threadpool.ThreadPool(
            self.__toal_thdnum, self.__toal_thdnum,
            name='executor_pool'
        )
        self.__status = 0  # 0 inited, 1 running 2 stopping
        log.info(
            'Executor service inited, delay_exec thread num:%d,'
            ' exec thread num:%d' % (delay_exe_thdnum, queue_exec_thdnum)
        )
        self._name = '' if name is None else name

    def _do_delay_exe(self, task_data):
        self.__delay_queue.put(task_data)

    def delay_exec(self,
        delay_time_insec, function, urgency, *args, **kwargs
    ):
        """
        delay_execute function after delay_time seconds

        You can use urgency := executor.URGENCY_NORMAL, by default

        :TODO:
            consider about stopping timers when invoking stop function
        """
        log.debug('got delay exec, func:{0}'.format(function))
        task_data = (urgency, (function, args, kwargs))
        timer = threading.Timer(
            delay_time_insec, self._do_delay_exe,
            [task_data]
        )
        timer.start()

    def queue_exec(self, function, urgency, *argvs, **kwargs):
        """
        execute function in a queue. Functions will be queued in line to
        be scheduled.

        You can use urgency := executor.URGENCY_NORMAL, by default.
        """
        task_data = (urgency, (function, argvs, kwargs))
        self.__exec_queue.put(task_data)

    def __exec_worker(self, check_interval, func_queue, worker_name=''):
        while self.__status != 2:
            try:
                item = func_queue.get(timeout=check_interval)
            except queue.Empty:
                continue
            function = None
            argvs = None
            kwargs = None
            try:
                _, (function, argvs, kwargs) = item
                # pylint: disable=W0142
                if func_queue is self.__delay_queue:
                    log.debug('to delay exec func:{0}'.format(function))
                function(*argvs, **kwargs)
            # pylint: disable=W0703
            # we can NOT predict the exception type
            except Exception as error:
                log.warn(
                    '{0} worker encountered exception:{1}, func:{2},'
                    'args:{3} {4} , executor service({5})'.format(
                    worker_name, error, function, argvs, kwargs, self._name)
                )
                log.warn('error type:{0}'.format(type(error)))
        log.debug(
            '%s worker thread exited as the service is stopping' % worker_name
        )

    def run(self):
        """
        Delayexec worker checks task every 20ms
        QueueExec worker checks task every 100ms
        """
        self.__thdpool.start()
        self.__status = 1
        for _ in range(0, self.__delay_exe_thdnum):
            self.__thdpool.add_1job(
                self.__exec_worker,
                0.1, self.__delay_queue,
                'Delayexec'
            )
        for _ in range(0, self.__queue_exe_thdnum):
            self.__thdpool.add_1job(
                self.__exec_worker, 0.02,
                self.__exec_queue,
                'Exec'
            )
        log.info('Executor service {0} started'.format(self._name))

    def start(self):
        """alias for self.run"""
        return self.run()

    def stop(self, wait_workerstop=True):
        """
        stop the executor service.

        :wait_workerstop:
            If wait_workerstop is True, the function will hang util all workers
            finish thier tasks.

            Otherwise, the function will not hang, but tell you whether it's
            succeeded stopped. (True for stoped, False for not stopped yet)
        """
        log.info('to stop executor {0}'.format(self._name))
        self.__status = 2
        if wait_workerstop:
            self.__thdpool.stop()
        else:
            self.__thdpool.try_stop()
        log.info('end stopping executor {0}'.format(self._name))

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
