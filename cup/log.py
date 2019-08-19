#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    common log related module
"""
from __future__ import print_function

__all__ = [
    'debug', 'info', 'warn', 'critical',
    'init_comlog', 'setloglevel',
    'ROTATION', 'INFINITE',
    'reinit_comlog', 'get_inited_loggername', 'parse',
    'backtrace_info', 'backtrace_debug', 'backtrace_error',
    'backtrace_critical'
]


import os
import re
import sys
import logging
import threading
from logging import handlers

import cup
from cup import err
from cup import platforms


ROTATION = 0
INFINITE = 1

ROTATION_COUNTS = 30
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
G_INITED_LOGGER = []


# pylint:disable=C0103
info = logging.info
warn = logging.warn
try:
    warn = logging.warning
except Exception:
    pass
error = logging.error
debug = logging.debug
critical = logging.critical


class _Singleton(object):  # pylint: disable=R0903
    """
    internal use for logging.  Plz use @Singoleton in cup.decorators
    """
    _LOCK = threading.Lock()

    def __init__(self, cls):
        self.__instance = None
        self.__cls = cls

    def __call__(self, *args, **kwargs):
        self._LOCK.acquire()
        if self.__instance is None:
            self.__instance = self.__cls(*args, **kwargs)
        self._LOCK.release()
        return self.__instance


# pylint: disable=R0903
class _MsgFilter(logging.Filter):
    """
    Msg filters by log levels
    """
    def __init__(self, msg_level=logging.WARNING):
        self.msg_level = msg_level

    def filter(self, record):
        if record.levelno >= self.msg_level:
            return False
        else:
            return True


# pylint: disable=R0903
@_Singleton
class _LoggerMan(object):
    _instance = None
    _pylogger = None
    _maxsize = 0
    _b_rotation = False
    _logfile = ''
    _logtype = ROTATION

    def __init__(self):
        pass

    def _getlogger(self):
        if self._pylogger is None:
            raise err.LoggerException(
                'The Cup logger has not been initalized Yet. '
                'Call init_comlog first'
            )
        return self._pylogger

    def _setlogger(self, logger):
        if self._pylogger is not None:
            raise err.LoggerException(
                """WARNING!!! The cup logger has been initalized already\
                .Plz do NOT init_comlog twice""")
        self._pylogger = logger

    def _reset_logger(self, logger):
        del self._pylogger
        self._pylogger = logger
        logging.root = logger

    def is_initalized(self):
        """
            Initialized or not
        """
        if self._pylogger is None:
            return False
        else:
            return True

    def _config_filelogger(
        self, loglevel, strlogfile, logtype, maxsize, bprint_console,
        gen_wf=False
    ):  # too many arg pylint: disable=R0913
        if not os.path.exists(strlogfile):
            try:
                os.mknod(strlogfile)
            except IOError:
                raise err.LoggerException(
                    'logfile does not exist. '
                    'try to create it. but file creation failed'
                )
        self._logfile = strlogfile
        self._logtype = logtype
        self._pylogger.setLevel(loglevel)
        self._maxsize = maxsize
        # '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s'
        formatter = logging.Formatter(
            '%(levelname)s:\t %(asctime)s * '
            '[%(process)d:%(thread)x] [%(filename)s:%(lineno)s] %(message)s'
        )
        if bprint_console:
            info('bprint_console enabled, will print to stdout')
            streamhandler = logging.StreamHandler()
            streamhandler.setLevel(loglevel)
            streamhandler.setFormatter(formatter)
            self._pylogger.addHandler(streamhandler)
        fdhandler = None
        if logtype == ROTATION:
            fdhandler = handlers.RotatingFileHandler(
                self._logfile, 'a', maxsize, ROTATION_COUNTS, encoding='utf-8'
            )
        else:
            fdhandler = logging.FileHandler(
                self._logfile, 'a', encoding='utf-8'
            )
        fdhandler.setFormatter(formatter)
        fdhandler.setLevel(loglevel)
        if gen_wf:
            # add .wf handler
            file_wf = str(self._logfile) + '.wf'
            warn_handler = logging.FileHandler(file_wf, 'a', encoding='utf-8')
            warn_handler.setLevel(logging.WARNING)
            warn_handler.setFormatter(formatter)
            self._pylogger.addHandler(warn_handler)
            fdhandler.addFilter(_MsgFilter(logging.WARNING))

        self._pylogger.addHandler(fdhandler)


def _line(back=0):
    return sys._getframe(back + 1).f_lineno  # traceback pylint:disable=W0212


def _file(back=0):
    # pylint:disable=W0212
    return os.path.basename(sys._getframe(back + 1).f_code.co_filename)


# def _func(back=0):
#     # traceback functionality. pylint:disable=W0212
#     return sys._getframe(back + 1).f_code.co_name \


def _proc_thd_id():
    # return str(os.getpid()) # traceback functionality. pylint:disable=W0212
    return str(os.getpid()) + ':' + str(threading.current_thread().ident)


def _log_file_func_info(msg, back_trace_len=0):
    tempmsg = ' * [%s] [%s:%s] ' % (
        _proc_thd_id(), _file(2 + back_trace_len),
        _line(2 + back_trace_len)
    )

    msg = '%s%s' % (tempmsg, msg)
    if isinstance(msg, unicode):
        return msg
    else:
        return msg.decode('utf8')


def init_comlog(
    loggername, loglevel=logging.INFO, logfile='cup.log',
    logtype=ROTATION, maxlogsize=1073741824, bprint_console=False,
    gen_wf=False
):  # too many arg pylint: disable=R0913
    """
    Initialize your logging

    :param loggername:
        Unique logger name
    :param loglevel:
        4 default levels: log.DEBUG log.INFO log.ERROR log.CRITICAL
    :param logfile:
        log file. Will try to create it if no existence
    :param logtype:
        Two type candidiates: log.ROTATION and log.INFINITE

        log.ROTATION will let logfile switch to a new one (30 files at most).
        When logger reaches the 30th logfile, will overwrite from the
        oldest to the most recent.

        log.INFINITE will write on the logfile infinitely
    :param maxlogsize:
        maxmum log size with byte
    :param b_printcmd:
        print to stdout or not?
    :param gen_wf:
        print log msges with level >= WARNING to file (${logfile}.wf)

    *E.g.*
    ::
        import logging
        from cup import log
        log.init_comlog(
            'test',
            log.DEBUG,
            '/home/work/test/test.log',
            log.ROTATION,
            1024,
            False
        )
        log.info('test xxx')
        log.critical('test critical')

    """
    loggerman = _LoggerMan()
    if not loggerman.is_initalized():
        # loggerman._setlogger(logging.getLogger(loggername))
        loggerman._setlogger(logging.getLogger())
        if os.path.exists(logfile) is False:
            if platforms.is_linux():
                os.mknod(logfile)
            else:
                with open(logfile, 'w+') as fhandle:
                    fhandle.write('----Windows File Creation ----\n')
        elif os.path.isfile(logfile) is False:
            raise err.LoggerException(
                'The log file exists. But it\'s not regular file'
            )
        loggerman._config_filelogger(
            loglevel, logfile, logtype, maxlogsize, bprint_console, gen_wf
        )  # too many arg pylint: disable=w0212
        info('-' * 20 + 'Log Initialized Successfully' + '-' * 20)
        global G_INITED_LOGGER
        G_INITED_LOGGER.append(loggername)
    else:
        print('[{0}:{1}] init_comlog has been already initalized'.format(
            _file(1), _line(1))
        )
    return


def reinit_comlog(
    loggername, loglevel=logging.INFO, logfile='cup.log',
    logtype=ROTATION, maxlogsize=1073741824, bprint_console=False,
    gen_wf=False
):  # too many arg pylint: disable=R0913
    """
    reinitalize logging system, paramters same to init_comlog.
    reinit_comlog will reset all logging parameters，
    Make sure you used a different loggername from the old one!
    """
    global G_INITED_LOGGER
    if loggername in G_INITED_LOGGER:
        msg = 'loggername:%s has been already initalized!!!' % loggername
        raise ValueError(msg)
    G_INITED_LOGGER.append(loggername)

    loggerman = _LoggerMan()
    loggerman._reset_logger(logging.getLogger(loggername))
    if os.path.exists(logfile) is False:
        if platforms.is_linux():
            os.mknod(logfile)
        else:
            with open(logfile, 'w+') as fhandle:
                fhandle.write('----Windows File Creation ----\n')
    elif os.path.isfile(logfile) is False:
        raise err.LoggerException(
            'The log file exists. But it\'s not regular file'
        )
    loggerman._config_filelogger(
        loglevel, logfile, logtype, maxlogsize, bprint_console, gen_wf
    )  # too many arg pylint: disable=w0212
    info('-' * 20 + 'Log Reinitialized Successfully' + '-' * 20)
    return


def get_inited_loggername():
    """
    get initialized logger name
    """
    global G_INITED_LOGGER
    return G_INITED_LOGGER


def _fail_handle(msg, e):
    if not isinstance(msg, unicode):
        msg = msg.decode('utf8')
    print('{0}\nerror:{1}'.format(msg, e))


def backtrace_info(msg, back_trace_len=0):
    """
    info with backtrace support
    """
    try:
        msg = _log_file_func_info(msg, back_trace_len)
        loggerman = _LoggerMan()
        loggerman._getlogger().info(msg)
    except err.LoggerException:
        return
    except Exception as e:
        _fail_handle(msg, e)


def backtrace_debug(msg, back_trace_len=0):
    """
    debug with backtrace support
    """
    try:
        msg = _log_file_func_info(msg, back_trace_len)
        loggerman = _LoggerMan()
        loggerman._getlogger().debug(msg)
    except err.LoggerException:
        return
    except Exception as e:
        _fail_handle(msg, e)


def backtrace_warn(msg, back_trace_len=0):
    """
    warning msg with backtrace support
    """
    try:
        msg = _log_file_func_info(msg, back_trace_len)
        loggerman = _LoggerMan()
        loggerman._getlogger().warn(msg)
    except err.LoggerException:
        return
    except Exception as e:
        _fail_handle(msg, e)


def backtrace_error(msg, back_trace_len=0):
    """
    error msg with backtarce support
    """
    try:
        msg = _log_file_func_info(msg, back_trace_len)
        loggerman = _LoggerMan()
        loggerman._getlogger().error(msg)
    except err.LoggerException:
        return
    except Exception as error:
        _fail_handle(msg, error)


def backtrace_critical(msg, back_trace_len=0):
    """
    logging.CRITICAL with backtrace support
    """
    try:
        msg = _log_file_func_info(msg, back_trace_len)
        loggerman = _LoggerMan()
        loggerman._getlogger().critical(msg)
    except err.LoggerException:
        return
    except Exception as e:
        _fail_handle(msg, e)


def setloglevel(logginglevel):
    """
    change log level during runtime
    """
    loggerman = _LoggerMan()
    loggerman._getlogger().setLevel(logginglevel)


def parse(logline):
    """
    return a dict if the line is valid.
    Otherwise, return None

    ::
        dict_info:= {
           'loglevel': 'DEBUG',
           'date': '2015-10-14',
           'time': '16:12:22,924',
           'pid': 8808,
           'tid': 1111111,
           'srcline': 'util.py:33',
           'msg': 'this is the log content'
        }

    """
    try:
        content = logline[logline.find(']'):]
        content = content[(content.find(']') + 1):]
        content = content[(content.find(']') + 1):].strip()
        regex = re.compile('[ \t]+')
        items = regex.split(logline)
        loglevel, date, time_, _, pid_tid, src = items[0:6]
        pid, tid = pid_tid.strip('[]').split(':')
        return {
            'loglevel': loglevel.strip(':'),
            'date': date,
            'time': time_,
            'pid': pid,
            'tid': tid,
            'srcline': src.strip('[]'),
            'msg': content
        }
    # pylint: disable = W0703
    except Exception:
        return None


def info_if(bol, msg, back_trace_len=1):
    """log msg with info loglevel if bol is true"""
    if bol:
        info(msg, back_trace_len)


def error_if(bol, msg, back_trace_len=1):
    """log msg with error loglevel if bol is true"""
    if bol:
        error(msg, back_trace_len)


def warn_if(bol, msg, back_trace_len=1):
    """log msg with error loglevel if bol is true"""
    if bol:
        warn(msg, back_trace_len)


def critical_if(bol, msg, back_trace_len=1):
    """log msg with critical loglevel if bol is true"""
    if bol:
        critical(msg, back_trace_len)


def debug_if(bol, msg, back_trace_len=1):
    """log msg with critical loglevel if bol is true"""
    if bol:
        debug(msg, back_trace_len)


if __name__ == '__main__':
    cup.log.debug('中文')
    cup.log.init_comlog(
        'test', cup.log.DEBUG, './test.log',
        cup.log.ROTATION, 102400000, False
    )
    cup.log.init_comlog(
        'test', cup.log.DEBUG, './test.log',
        cup.log.ROTATION, 102400000, False
    )
    cup.log.info('test info')
    cup.log.debug('test debug')
    cup.log.info('中文'.decode('utf8'))
    cup.log.reinit_comlog(
        're-test', cup.log.DEBUG, './re.test.log',
        cup.log.ROTATION, 102400000, False
    )
    cup.log.reinit_comlog(
        're-test', cup.log.DEBUG, './re.test.log',
        cup.log.ROTATION, 102400000, False
    )
    cup.log.info('re:test info')
    cup.log.debug('re:test debug')
    cup.log.debug('re:中文')


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
