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
    Guannan ported threadpool from twisted.python.
    Mit License applied for twisted.
    http://www.opensource.org/licenses/mit-license.php
    if any concern, plz contact Guannan at mythmgn@gmail.com
"""

try:
    import Queue as queue
except ImportError:
    # pylint: disable=F0401
    import queue
import contextlib
import threading
import copy
import sys
# import traceback

import cup
from cup import log
from cup.util import context

_CONTEXT_TRACKER = context.ContextTracker4Thread()


class ThreadPool(object):
    """
    Threadpool class
    """

    _THREAD_FACTORY = threading.Thread
    _CURRENT_THREAD = staticmethod(threading.current_thread)
    _WORKER_STOP_SIGN = object()

    def __init__(self, minthreads=5, maxthreads=20, name=None):
        """
        创建一个线程池。
        :param minthreads:
            最少多少个线程在工作。
        :param maxthreads:
            最多多少个线程在工作
        """
        assert minthreads > 0, 'minimum must be >= 0 '
        assert minthreads <= maxthreads, 'minimum is greater than maximum'

        self._min = 5
        self._max = 20
        self._joined = False
        self._started = False
        self._workers = 0
        self._name = None
        # Queue is a thread-safe queue
        self._jobqueue = queue.Queue(0)
        self._min = minthreads
        self._max = maxthreads
        self._name = name
        self._waiters = []
        self._threads = []
        self._working = []

    def start(self):
        """
        启动线程池
        """
        self._joined = False
        self._started = True
        # Start some threads.
        self.adjust_poolsize()

    def start1worker(self):
        """
        为线程池增加一个线程。
        """
        self._workers += 1
        name = "PoolThread-%s-%s" % (self._name or id(self), self._workers)
        new_thd = self._THREAD_FACTORY(target=self._worker, name=name)
        self._threads.append(new_thd)
        new_thd.start()

    def stop1worker(self):
        """
        为线程池减少一个线程。
        """
        self._jobqueue.put(self._WORKER_STOP_SIGN)
        self._workers -= 1

    def __setstate__(self, state):
        """
        For pickling an instance from a serilized string
        """
        self.__dict__ = state
        self.__class__.__init__(self, self._min, self._max)

    def __getstate__(self):
        state = {}
        state['min'] = self._min
        state['max'] = self._max
        return state

    def _start_decent_workers(self):
        need_size = self._jobqueue.qsize() + len(self._working)
        # Create enough, but not too many
        while self._workers < min(self._max, need_size):
            self.start1worker()

    def add_1job(self, func, *args, **kwargs):
        """
        :param func:
            会被线程池调度的函数

        :param *args:
            func函数需要的参数

        :param **kw:
            func函数需要的kwargs参数
        """
        # log.info('add 1job[{0}]'.format(func))
        self.add_1job_with_callback(None, func, *args, **kwargs)

    def add_1job_with_callback(self, result_callback, func, *args, **kwargs):
        """
        :param result_callback:
            func作业处理函数被线程池调用后，无论成功与否都会
            执行result_callback.

            result_callback函数需要有两个参数
            (ret_in_bool, result), 成功的话为(True, result), 失败的话
            为(False, result)

            如果func raise exception, result_callback会收到(False, failure)

        :param func:
            同add_1job, 被调度的作业函数

        :param *args:
            同add_1job, func的参数

        :param **kwargs:
            同add_1job, func的kwargs参数
        """
        if self._joined:
            return
        # pylint: disable=W0621
        context = _CONTEXT_TRACKER.current_context().contexts[-1]
        job = (context, func, args, kwargs, result_callback)
        self._jobqueue.put(job)
        if self._started:
            self._start_decent_workers()

    @contextlib.contextmanager
    def _worker_state(self, state_list, worker_thread):
        state_list.append(worker_thread)
        try:
            yield
        finally:
            state_list.remove(worker_thread)

    def _log_err_context(self, context):
        log.warn(
            'Seems a call with context failed. See the context info'
        )
        log.warn(str(context))

    def _worker(self):
        """
        worker func to handle jobs
        """
        current_thd = self._CURRENT_THREAD()
        with self._worker_state(self._waiters, current_thd):
            job = self._jobqueue.get()

        while job is not self._WORKER_STOP_SIGN:
            with self._worker_state(self._working, current_thd):
                # pylint: disable=W0621
                context, function, args, kwargs, result_callback = job
                del job

                try:
                    # pylint: disable=W0142
                    result = _CONTEXT_TRACKER.call_with_context(
                        context, function, *args, **kwargs
                    )
                    success = True
                except Exception as error:
                    success = False
                    log.warn(
                        'Func failed, func:%s, error_msg: %s'  %
                        (str(function), str(error))
                    )
                    if result_callback is None:
                        log.warn('This func does not have callback.')
                        _CONTEXT_TRACKER.call_with_context(
                            context, self._log_err_context, context
                        )
                        result = None
                    else:
                        result = error

                del function, args, kwargs
            # when out of  "with scope",
            # the self._working will remove the thread from
            # its self._working list

            if result_callback is not None:
                try:
                    _CONTEXT_TRACKER.call_with_context(
                        context, result_callback, success, result
                    )
                except Exception as e:
                    # traceback.print_exc(file=sys.stderr)
                    log.warn(
                        'result_callback func failed, callback func:%s,'
                        'err_msg:%s' % (str(result_callback), str(e))
                    )
                    _CONTEXT_TRACKER.call_with_context(
                        context, self._log_err_context, context
                    )

            del context, result_callback, result

            with self._worker_state(self._waiters, current_thd):
                job = self._jobqueue.get()
            # after with statements, self._waiters will remove current_thd

        # remove this thread from the list
        self._threads.remove(current_thd)

    def stop(self):
        """
        停止线程池， 该操作是同步操作， 会夯住一直等到线程池所有线程退出。
        """
        self._joined = True
        threads = copy.copy(self._threads)
        while self._workers:
            self._jobqueue.put(self._WORKER_STOP_SIGN)
            self._workers -= 1

        # and let's just make sure
        # FIXME: threads that have died before calling stop() are not joined.
        for thread in threads:
            thread.join()

    def try_stop(self, check_interval=0.1):
        """
        发送停止线程池命令， 并尝试查看是否stop了。 如果没停止，返回False

        try_stop不会夯住， 会回返。 属于nonblocking模式下
        """
        self._joined = True
        threads = copy.copy(self._threads)
        while self._workers:
            self._jobqueue.put(self._WORKER_STOP_SIGN)
            self._workers -= 1

        for thread in threads:
            thread.join(check_interval)

        for thread in threads:
            if thread.isAlive:
                return False

        return True

    def adjust_poolsize(self, minthreads=None, maxthreads=None):
        """
        调整线程池的线程最少和最多运行线程个数
        """
        if minthreads is None:
            minthreads = self._min
        if maxthreads is None:
            maxthreads = self._max

        assert minthreads >= 0, 'minimum is negative'
        assert minthreads <= maxthreads, 'minimum is greater than maximum'

        self._min = minthreads
        self._max = maxthreads
        if not self._started:
            return

        # Kill of some threads if we have too many.
        while self._workers > self._max:
            self.stop1worker()
        # Start some threads if we have too few.
        while self._workers < self._min:
            self.start1worker()
        # Start some threads if there is a need.
        self._start_decent_workers()

    def get_stats(self):
        """
        回返当前threadpool的状态信息.
        其中queue_len为当前threadpool排队的作业长度
        waiters_num为当前空闲的thread num
        working_num为当前正在工作的thread num
        thread_num为当前一共可以使用的thread num::
            stat = {}
            stat['queue_len'] = self._jobqueue.qsize()
            stat['waiters_num'] = len(self._waiters)
            stat['working_num'] = len(self._working)
            stat['thread_num'] = len(self._threads)
        """
        stat = {}
        stat['queue_len'] = self._jobqueue.qsize()
        stat['waiters_num'] = len(self._waiters)
        stat['working_num'] = len(self._working)
        stat['thread_num'] = len(self._threads)
        return stat

    def dump_stats(self, print_stdout=False):
        """
        打印当前threadpool的状态信息到log 和stdout
        其中状态信息来自于get_stats函数
        """
        stat = self.get_stats()
        if print_stdout:
            print stat
        log.info('ThreadPool Stat %s: %s' % (self._name, stat))
        log.debug('queue: %s' % self._jobqueue.queue)
        log.debug('waiters: %s' % self._waiters)
        log.debug('workers: %s' % self._working)
        log.debug('total: %s' % self._threads)
        return stat
