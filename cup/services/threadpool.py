#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
:description:
    Guannan back-ported threadpool from twisted.python.
    if any concern, plz contact Guannan (mythmgn@gmail.com)

:license:
    Mit License applied for twisted:
        http://www.opensource.org/licenses/mit-license.php

        Permission is hereby granted, free of charge,
        to any person obtaining a copy of this software and associated
        documentation files (the "Software"),
        to deal in the Software without restriction,
        including without limitation the rights to use, copy, modify, merge,
        publish, distribute, sublicense, and/or sell copies of the Software,
        and to permit persons to whom the Software is furnished to do so,
        subject to the following conditions:

        The above copyright notice and this permission notice shall be
        included in all copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
        EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
        MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
        IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
        CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
        TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
        WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from __future__ import print_function
try:
    import Queue as queue
except ImportError:
    # pylint: disable=F0401
    import queue
import copy
import time
import traceback
import contextlib
import threading

from cup import log
from cup.util import context
from cup import thread

_CONTEXT_TRACKER = context.ContextTracker4Thread()


# pylint: disable=R0902
class ThreadPool(object):
    """
    Threadpool class
    """
    _THREAD_FACTORY = thread.CupThread
    _CURRENT_THREAD = staticmethod(threading.current_thread)
    _WORKER_STOP_SIGN = object()

    def __init__(
        self, minthreads=5, maxthreads=20, name=None, daemon_threads=False):
        """
        create a threadpool

        :param minthreads:
            minimum threads num

        :param maxthreads:
            maximum threads num

        :param daemon_threads:
            daemon threads or not.

            Notice if daemon_threads is True, threadpool will exit as soon
            as the main thread exits. Otherwise, all worker threads will exit
            after you explicitly call the class method (or try_stop)
        """
        assert minthreads > 0, 'minimum must be >= 0 '
        assert minthreads <= maxthreads, 'minimum is greater than maximum'

        self._min = 5
        self._max = 20
        self._joined = False
        self._started = False
        self._workers = 0
        self._name = None
        self._daemon_thread = daemon_threads
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
        call start before you use the threadpool
        """
        self._joined = False
        self._started = True
        # Start some threads.
        self.adjust_poolsize()

    def start1worker(self):
        """
        add a thread for worker threads in the pool
        """
        self._workers += 1
        name = "PoolThread-%s-%s" % (self._name or id(self), self._workers)
        new_thd = self._THREAD_FACTORY(target=self._worker, name=name)
        if self._daemon_thread:
            new_thd.daemon = True
        self._threads.append(new_thd)
        new_thd.start()

    def stop1worker(self):
        """
        decrease one thread for the worker threads
        """
        self._jobqueue.put(self._WORKER_STOP_SIGN)
        self._workers -= 1

    def __setstate__(self, state):
        """
        For pickling an instance from a serilized string
        """
        # pylint: disable=W0201
        # set up state for it
        self.__dict__ = state
        self.__class__.__init__(self, self._min, self._max)

    def __getstate__(self):
        state = {}
        state['min'] = self._min
        state['max'] = self._max
        return state

    def _start_decent_workers(self):
        """ start decent/proper number of thread workers"""
        need_size = self._jobqueue.qsize() + len(self._working)
        # Create enough, but not too many
        while self._workers < min(self._max, need_size):
            self.start1worker()

    def add_1job(self, func, *args, **kwargs):
        """
        Add one job that you want the pool to schedule.
        Notice if you need to handle data after finishing [func], plz use
        [add_1job_with_callback] which supports a [callback] option.

        :param func:
            function that will be scheduled by the thread pool

        :param *args:
            args that the [func] needs

        :param **kw:
            kwargs that [func] needs
        """
        self.add_1job_with_callback(None, func, *args, **kwargs)

    def add_1job_with_callback(self, result_callback, func, *args, **kwargs):
        """
        :param result_callback:
            plz notice whether succeed or fail, the result_callback function
            will be called after [func] is called.

            function result_callback needs to accept two parameters:
            (ret_in_bool, result). (True, result) will be passed to the [func]
            on success. (False, result) will be passed otherwise.

            if [func] raise any Exception, result_callback will get (False,
                failure_info) as well.

        :param func:
            same to func for add_1job

        :param *args:
            args for [func]

        :param **kwargs:
            kwargs for [func]
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
        """
        worker state
        """
        state_list.append(worker_thread)
        try:
            yield
        finally:
            state_list.remove(worker_thread)

    def _log_err_context(self, context):
        """
        context error, log warning msg
        """
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
                        'Func failed, func:{0}, error_msg: {1}'.format(
                        function, error)
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

    def stop(self, force_stop=False):
        """
        stop the thread pool. Notice calling this method will wait there util
        all worker threads exit.

        :force_stop:
            if force_stop is True, try to stop the threads in the pool
            immediately (and this may do DAMAGE to your code logic)
        """
        if not force_stop:
            self._joined = True
            threads = copy.copy(self._threads)
            while self._workers:
                self._jobqueue.put(self._WORKER_STOP_SIGN)
                self._workers -= 1
            for thd in threads:
                thd.join()
        else:
            for thd in self._threads:
                thd.terminate()
            retry = False
            times = 0
            while not retry and (times <= 100):
                for thd in self._threads:
                    if thd.isAlive():
                        thd.terminate()
                        retry = True
                time.sleep(0.1)
                times += 1

    def try_stop(self, check_interval=0.1):
        """
        try to stop the threadpool.

        If it cannot stop the pool RIGHT NOW, will NOT block.
        """
        self._joined = True
        threads = copy.copy(self._threads)
        while self._workers:
            self._jobqueue.put(self._WORKER_STOP_SIGN)
            self._workers -= 1

        for thd in threads:
            thd.join(check_interval)

        for thd in threads:
            if thd.isAlive():
                return False

        return True

    def adjust_poolsize(self, minthreads=None, maxthreads=None):
        """
        adjust pool size
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
        get threadpool running stats
        waiters_num is pending thread num
        working_num is working thread num
        thread_num is the total size of threads

        ::
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
        Dump the threadpool stat to log or stdout. Info is from class method
        [get_stats]
        """
        stat = self.get_stats()
        if print_stdout:
            print(stat)
        log.info('ThreadPool Stat %s: %s' % (self._name, stat))
        log.debug('queue: %s' % self._jobqueue.queue)
        log.debug('waiters: %s' % self._waiters)
        log.debug('workers: %s' % self._working)
        log.debug('total: %s' % self._threads)
        return stat
