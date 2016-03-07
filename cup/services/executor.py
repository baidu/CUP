#!/usr/bin/env python
# -*- coding: utf-8 -*
# #############################################################
#
#  Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#
# #############################################################
"""
:authors:
    Guannan Ma maguannan@baidu.com @mythmgn
:create_date:
    2015/07/01
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

from cup.util import threadpool
from cup import log
# import Queue as queue

class ExecutionService(object):
    def __init__(
        self, delay_exe_thdnum=3, queue_exec_thdnum=4
    ):
        self.__toal_thdnum = delay_exe_thdnum + queue_exec_thdnum
        self.__delay_exe_thdnum = delay_exe_thdnum
        self.__queue_exe_thdnum = queue_exec_thdnum
        self.__delay_queue = queue.PriorityQueue()
        self.__exec_queue = queue.PriorityQueue()
        self.__thdpool = threadpool.ThreadPool(
            self.__toal_thdnum, self.__toal_thdnum
        )
        self.__status = 0  # 0 inited, 1 running 2 stopping
        log.info(
            'Executor service inited, delay_exec thread num:%d,'
            ' exec thread num:%d' % (delay_exe_thdnum, queue_exec_thdnum)
        )

    def _do_delay_exe(self, task_data):
        self.__delay_queue.put(task_data)

    def delay_exec(self, delay_time_insec, function, data, urgency=1):
        """
        delay_execute function after delay_time seconds

        urgency := [0|1|2]. 0 is most urgent. 1 is normal. 2 is lest urgent
        """
        task_data = (urgency, (function, data))
        timer = threading.Timer(
            delay_time_insec, self._do_delay_exe,
            [task_data]
        )
        timer.start()

    def queue_exec(self, function, data, urgency=1):
        """
        execute function in a queue. Functions will be queued in line to
        be scheduled.

        urgency := [0|1|2]. 0 is most urgent. 1 is normal. 2 is lest urgent
        """
        task_data = (urgency, (function, data))
        self.__exec_queue.put(task_data)

    def __exec_worker(self, check_interval, func_queue, worker_name=''):
        while self.__status != 2:
            try:
                item = func_queue.get(timeout=check_interval)
            except queue.Empty:
                log.debug('no item found in exec queue')
                continue
            try:
                _, (function, data) = item
                function(data)
            # pylint: disable=W0703
            # we can NOT predict the exception type
            except Exception as error:
                log.warn(
                    '%s worker encountered exception:%s, func:%s, data:%s' %
                    (worker_name, error, function, data)
                )
        log.info(
            '%s worker thread exited as the service is stopping' % worker_name
        )

    def run(self):
        """
        Delayexec worker checks task every 20ms
        QueueExec worker checks task every 100ms
        """
        self.__thdpool.start()
        self.__status = 1
        for _ in xrange(0, self.__delay_exe_thdnum):
            self.__thdpool.add_1job(
                self.__exec_worker,
                0.1, self.__delay_queue,
                'Delayexec'
            )
        for _ in xrange(0, self.__queue_exe_thdnum):
            self.__thdpool.add_1job(
                self.__exec_worker, 0.02,
                self.__exec_queue,
                'Exec'
            )
        log.info('Executor service started')

    def stop(self, wait_workerstop=True):
        """
        stop the executor service.

        :wait_workerstop:
            If wait_workerstop is True, the function will hang util all workers
            finish thier tasks.

            Otherwise, the function will not hang, but tell you whether it's
            succeeded stopped. (True for stoped, False for not stopped yet)
        """
        self.__status = 2
        if wait_workerstop:
            self.__thdpool.stop()
        else:
            self.__thdpool.try_stop()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
