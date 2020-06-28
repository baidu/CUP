#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    1. Delay-execute sth after several seconds

    2. Schedule some tasks in a queue.
"""
from __future__ import print_function
import abc
import pdb
try:
    # pylint:disable=F0401
    import queue
except ImportError:
    import Queue as queue
import copy
import time
import calendar
import datetime
import threading
import traceback

import pytz
from cup.util import threadpool
from cup import log
from cup.services import generator

URGENCY_HIGH = 0
URGENCY_NORMAL = 1
URGENCY_LOW = 2


class AbstractExecution(object):
    """
    abstract execution service
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, delay_exe_thdnum, queue_exec_thdnum, name):
        """
        init
        """
        self._toal_thdnum = delay_exe_thdnum + queue_exec_thdnum
        self._delay_exe_thdnu = delay_exe_thdnum
        self._queue_exe_thdnum = queue_exec_thdnum
        self._delay_queue = queue.PriorityQueue()
        self._exec_queue = queue.PriorityQueue()
        self._thdpool = threadpool.ThreadPool(
            self._toal_thdnum, self._toal_thdnum,
            name='executor_pool'
        )
        self._status = 0  # 0 inited, 1 running 2 stopping
        log.info(
            'Executor service inited, delay_exec thread num:%d,'
            ' exec thread num:%d' % (delay_exe_thdnum, queue_exec_thdnum)
        )
        self._name = '' if name is None else name

    @abc.abstractmethod
    def exec_worker(self, check_interval, func_queue, worker_name):
        """exec worker"""

    @abc.abstractmethod
    def delay_exec(self,
        delay_time_insec, function, urgency, *args, **kwargs
    ):
        """delay exec for the abstract"""


class ExecutionService(AbstractExecution):
    """
    execution service
    """
    def __init__(
        self, delay_exe_thdnum=3, queue_exec_thdnum=4, name=None
    ):
        AbstractExecution.__init__(
            self, delay_exe_thdnum, queue_exec_thdnum, name
        )

    def _do_delay_exe(self, task_data):
        self._delay_queue.put(task_data)

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
        self._exec_queue.put(task_data)

    def exec_worker(self, check_interval, func_queue, worker_name=''):
        while self._status != 2:
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
                if func_queue is self._delay_queue:
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
            '{0} worker thread exited as the service '
            'is stopping'.format(worker_name)
        )

    def run(self):
        """
        Delayexec worker checks task every 20ms
        QueueExec worker checks task every 100ms
        """
        self._thdpool.start()
        self._status = 1
        for _ in range(0, self._delay_exe_thdnu):
            self._thdpool.add_1job(
                self.exec_worker,
                0.1, self._delay_queue,
                'Delayexec'
            )
        for _ in range(0, self._queue_exe_thdnum):
            self._thdpool.add_1job(
                self.exec_worker, 0.02,
                self._exec_queue,
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
        self._status = 2
        if wait_workerstop:
            self._thdpool.stop()
        else:
            self._thdpool.try_stop()
        log.info('end stopping executor {0}'.format(self._name))


class CronTask(object):
    """
    crontask for CronExecution

    Typical exmaples for timer_dict:

    1) one specific time  Jan 1st, 2020 18:01
        timer_dict {
            'minute': [1], 'hour': [18], 'weekday': None,
            'monthday': [1], 'month': [1]
        }
    2) every minute {
        timer_dict {
                'minute': [0, 1, 2, ....59], 'hour': None, 'weekday': None,
                'monthday': None, 'month': None
        }
    3) every hour
        timer_dict {
                'minute': [0], 'hour': None, 'weekday': None,
                'monthday': None, 'month': None
        }
    4) every 20:00 PM
        timer_dict {
            'minute': [0], 'hour': [20], 'weekday': None,
            'monthday': None, 'month': None
        }
    5) every 20:00 PM at workdays (Monday to Friday)
        timer_dict {
                'minute': [0], 'hour': [20], 'weekday': [1, 2, 3, 4, 5],
                'monthday': None, 'month': None
        }
    6) every 20:00 PM at workdays for Jan and July
        timer_dict {
            'minute': [0], 'hour': [20], 'weekday': [1, 2, 3, 4, 5],
            'monthday': None, 'month': [1, 7]
        }
    7) every 20:00 PM at 1st, 3rd of Jan and July
        timer_dict {
            'minute': [0], 'hour': [20], 'weekday': None,
            'monthday': [1, 3], 'month': [1, 7]
        }
    """

    _CHECK_ORDER = ['month', 'monthday', 'weekday', 'hour', 'minute']
    _NONE_FILLING = {
        'month': range(1, 13),
        'monthday': range(1, 32),
        'weekday': range(1, 8),
        'hour': range(24),
        'minute': range(60)
    }
    _GEN = generator.CachedUUID()

    def __init__(
        self, name, pytz_timezone, timer_dict, md5uuid,
        function, *args, **kwargs
    ):
        """
        :param pytz_timezone:
            which can be initialized like: tz = pytz.timezone('Asia/Beijing')
        :param timer_dict:
            {   'minute': minute_list,
                'hour': hour_list,
                'weekday': weekday_list,    # [1~7]
                'monthday': monday_list,    # [1~31]
                'month': month_list,         # [1~12, 1~12]
            } # None stands for all valid, don't consider this field
        :param function:
            function that to be scheduled
        :param args:
            args of function
        :param kwargs:
            key args of function

        :raise:
            ValueError if function is not callable
        """
        if not callable(function):
            raise ValueError('param function should be callable')
        if not isinstance(pytz_timezone, pytz.BaseTzInfo):
            raise ValueError('not a valid pytz timezone')
        self._name = name
        self._funcargs = (function, args, kwargs)
        self._pytz = pytz_timezone
        self._timer_dict = timer_dict
        if not all([
            'minute' in timer_dict,
            'hour' in timer_dict,
            'weekday' in timer_dict,
            'monthday' in timer_dict,
            'month' in timer_dict
        ]):
            raise ValueError('keys '
                '(minute hour weekday monthday month should be in dict)'
            )
        self._timer_params = self._generate_timer_params(self._timer_dict)
        self._check_param_valids(self._timer_params)
        self._lastsched_time = None
        if md5uuid is None:
            self._md5_id = self._GEN.get_uuid()[0]
        else:
            self._md5_id = md5uuid
        self._timer = None

    def get_funcargs(self):
        """return (function, args, kwargs)"""
        return self._funcargs

    def name(self):
        """return name of the crontask"""
        return self._name

    def taskid(self):
        """get 32 byte taskid"""
        return self._md5_id

    def last_schedtime(self):
        """return last schedtime"""
        return self._lastsched_time

    def _generate_timer_params(self, timer_dict):
        """generate timer params"""
        tmp_timer_dict = {}
        for check_key in self._CHECK_ORDER:
            valid_items = timer_dict[check_key]
            if valid_items is None:
                tmp_timer_dict[check_key] = self._NONE_FILLING[check_key]
            else:
                tmp_timer_dict[check_key] = sorted(valid_items)
        return tmp_timer_dict

    def pytz_timezone(self):
        """return pytz timezone"""
        return self._pytz

    def set_last_schedtime(self, datetime_obj):
        """set_last_schedtime.

        :param timestamp:
            E.g. set timestamp to time.time() for "now"
        """
        if not isinstance(datetime_obj, datetime.datetime):
            raise ValueError('datetime_obj should be a datetime.datetime obj')
        self._lastsched_time = datetime_obj

    def get_last_schedtime(self):
        """get last sched time, return with a datetime.datetime object.
        Plz notice the timezone is enabled
        """
        return self._lastsched_time

    @classmethod
    def _check_param_valids(cls, timer_params):
        """
        check if params r valid

        :raise:
            ValueError if not valid
        """
        for check_key in timer_params:
            if len(timer_params[check_key]) < 1:
                raise ValueError('{0} less than 1 element'.format(check_key))

    @classmethod
    def next_month(cls, tmp_dict, timer_params):
        """
        set tmp_dict to next valid date, specifically month

        :param tmp_dict:
            {
                'year': xxxx,
                'month': xxxx,
                'monthday': xxxx,
                'weekday': xxxx,
                'hour': xxxx,
                'minute': xxxx
            }
        :param timer_params:
            valid timer dict, same to self._timer_params
        """
        while True:
            tmp_dict['month'] += 1
            if tmp_dict['month'] in timer_params['month']:
                break
            else:
                if tmp_dict['month'] > 12:
                    tmp_dict['month'] = timer_params['month'][0]
                    tmp_dict['year'] += 1
                    break
        monthday = [x for x in
            range(
                1,
                calendar.monthrange(tmp_dict['year'], tmp_dict['month'])[1] + 1
            ) \
            if x in timer_params['monthday']
        ]
        tmp_dict['monthday'] = monthday[0]
        tmp_dict['hour'] = timer_params['hour'][0]
        tmp_dict['minute'] = timer_params['minute'][0]
        tmp_dict['weekday'] = calendar.weekday(
            tmp_dict['year'], tmp_dict['month'], tmp_dict['monthday']
        ) + 1
        timer_params['monthday'] = monthday

    @classmethod
    def check_monthday_weekday(cls, tmp_dict, timer_params):
        """check if monthday / weekday valid"""
        try:
            day = calendar.weekday(
                tmp_dict['year'], tmp_dict['month'], tmp_dict['monthday']
            ) + 1
        # e.g.  invalid date, 4.31
        except ValueError:
            return False
        if day in timer_params['weekday']:
            return True
        else:
            return False

    @classmethod
    def next_monthday_weekday(cls, tmp_dict, timer_params):
        """
        set next monthday && weekday
        """
        plus = 1
        while True:
            tmp_dict['monthday'] += plus
            if plus == 0:
                plus = 1
            if all([
                tmp_dict['monthday'] in timer_params['monthday'],
                cls.check_monthday_weekday(tmp_dict, timer_params)
            ]):
                tmp_dict['hour'] = timer_params['hour'][0]
                tmp_dict['minute'] = timer_params['hour'][0]
                break
            else:
                if tmp_dict['monthday'] > 31:
                    cls.next_month(tmp_dict, timer_params)
                    plus = 0

    @classmethod
    def next_hour(cls, tmp_dict, timer_params):
        """
        :return:
            { 'year': xxx,
              'month': xxx,
              'monthday':
        """
        plus = 1
        while True:
            tmp_dict['hour'] += plus
            if plus == 0:
                plus = 1
            if tmp_dict['hour'] in timer_params['hour']:
                tmp_dict['minute'] = timer_params['minute'][0]
                break
            else:
                if tmp_dict['hour'] > 23:
                    cls.next_monthday_weekday(tmp_dict, timer_params)
                    plus = 0

    @classmethod
    def next_minute(cls, tmp_dict, timer_params):
        """
        :return:
            { 'year': xxx,
              'month': xxx,
              'monthday':
        """
        plus = 1
        while True:
            tmp_dict['minute'] += plus
            if plus == 0:
                plus = 1
            if tmp_dict['minute'] in timer_params['minute']:
                break
            else:
                if tmp_dict['minute'] > 59:
                    cls.next_hour(tmp_dict, timer_params)
                    plus = 0

    def next_schedtime(self, starting_fromdate=None):
        """
        return next schedule time with timezone enabled.
        """
        if starting_fromdate is None:
            tmp = datetime.datetime.now()
            datenow = self._pytz.localize(tmp)
        else:
            datenow = starting_fromdate
        tmp_dict = {
            'year': datenow.year,
            'month': datenow.month,
            'monthday': datenow.day,
            'weekday': datenow.isoweekday(),
            'hour': datenow.hour,
            'minute': datenow.minute + 1
        }
        timer_params = copy.deepcopy(self._timer_params)
        maxtimes = 365 * 24 * 60
        while True:
            if tmp_dict['month'] in timer_params['month']:
                if self.check_monthday_weekday(
                    tmp_dict, timer_params
                ):
                    if tmp_dict['hour'] in timer_params['hour']:
                        if tmp_dict['minute'] in timer_params['minute']:
                            break
                        else:
                            self.next_minute(tmp_dict, self._timer_params)
                        maxtimes -= 1
                        if maxtimes < 0:
                            log.warn(
                                'No valid datetime in a year'
                                'for crontask {0}'.format(self)
                            )
                            return None
                    else:
                        self.next_hour(tmp_dict, self._timer_params)
                else:
                    self.next_monthday_weekday(tmp_dict, self._timer_params)
            else:
                self.next_month(tmp_dict, timer_params)

        local_dt = self._pytz.localize(datetime.datetime(
            year=tmp_dict['year'],
            month=tmp_dict['month'],
            day=tmp_dict['monthday'],
            hour=tmp_dict['hour'],
            minute=tmp_dict['minute']
        ))
        self.set_last_schedtime(local_dt)
        return local_dt

    def __repr__(self):
        """return info of the crontask"""
        return 'CronTask(ID:{0} Name:{1})'.format(self.taskid(), self._name)

    def set_timer(self, timer):
        """set timer to this crontask"""
        self._timer = timer

    def get_timer(self):
        """return timer of the crontask"""
        return self._timer


class CronExecution(ExecutionService):
    """
    run execution like cron.

    Plz notice the following circumstances:
        - if the previous task is still running and the scheduing time comes,
            executor will wait until the previous task finishes

    """
    def __init__(self, threads_num=3, name=None):
        """
        :param threads_num:
            startup threads num
        :param max_threadsnum:
            max threads num
        """
        self._task_dict = {}
        ExecutionService.__init__(
            self, delay_exe_thdnum=threads_num, queue_exec_thdnum=0,
            name=name
        )

    def get_tasks(self):
        """get all cron execution tasks"""
        return self._task_dict.items()

    def get_taskbyid(self, md5uuid):
        """
        :param md5uuid:
            md5sum of uuid
        """
        return self._task_dict.get(md5uuid, None)

    def exec_worker(self, check_interval, func_queue, worker_name=''):
        log.info('CronExecution exec worker started')
        while self._status != 2:
            try:
                item = func_queue.get(timeout=check_interval)
            except queue.Empty:
                continue
            function = None
            argvs = None
            kwargs = None
            try:
                _, crontask, (function, argvs, kwargs) = item
                # pylint: disable=W0142
                if func_queue is self._delay_queue:
                    log.debug('to delay exec func:{0}'.format(function))
                dtnow = datetime.datetime.now(crontask.pytz_timezone())
                if (dtnow - crontask.get_last_schedtime()).total_seconds() > 60:
                    log.warn(
                        'lagging crontask found (name:{0} id: {1})'.format(
                            crontask.name(), crontask.taskid()
                        )
                    )
                function(*argvs, **kwargs)
                self.schedule(crontask)
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
            '{0} worker thread exited as the service '
            'is stopping'.format(worker_name)
        )

    def delay_exec(self,
        delay_time_insec, crontask, function, urgency, *args, **kwargs
    ):
        """
        delay_execute function after delay_time seconds

        You can use urgency := executor.URGENCY_NORMAL, by default

        :TODO:
            consider about stopping timers when invoking stop function
        """
        log.info(
            'CronExecution {0} got delay exec, func:{1}'.format(
                self._name, function)
        )
        task_data = (urgency, crontask, (function, args, kwargs))
        timer = threading.Timer(
            delay_time_insec, self._do_delay_exe,
            [task_data]
        )
        crontask.set_timer(timer)
        timer.start()

    def schedule(self, crontask):
        """schedule.

        :param timer_dict:
            {   'minute': minute_list,
                'hour': hour_list,
                'weekday': weekday_list,
                'monthday': monday_list,
                'month': month_list
            }
        :param function:
            function that to be scheduled
        :param args:
            args of function
        :param kwargs:
            key args of function
        """
        next_schedtime = crontask.next_schedtime()
        if next_schedtime is None:
            log.warn(
                'CronExecution:crontask {0} will be deleted '
                'from the crontask as '
                'no valid schedule time is found'.format(crontask)
            )
        function, args, kwargs = crontask.get_funcargs()
        tmpnow = crontask.pytz_timezone().localize(datetime.datetime.now())
        wait_seoncds = (next_schedtime - tmpnow).total_seconds()
        log.info(
            'CronExecution: next schedule time for this crontask is {0} '
            'timezone {1}, wait for {2} seconds, timenwo is {3}'.format(
                next_schedtime, next_schedtime.tzinfo,
                wait_seoncds,
                next_schedtime.tzinfo.localize(datetime.datetime.now())
            )
        )
        # pylint: disable=W0142
        self.delay_exec(
            wait_seoncds, crontask, function, URGENCY_NORMAL, *args, **kwargs
        )
        self._task_dict[crontask.taskid()] = crontask

    def calcel_delay_exec(self, taskid):
        """calcel delayexec by taskid"""
        task = self._task_dict.get(taskid, None)
        if task is None:
            log.warn('delay exec task id {0} not found'.format(taskid))
            return
        timer = task.get_timer()
        timer.cancel()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
