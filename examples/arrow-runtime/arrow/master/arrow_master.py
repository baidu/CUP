#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
:authors:
    Guannan Ma @mythmgn
:create_date:
    2016/05/05
:description:
    TODO:
        1. Heartbeat with resource
        2. Serialize base for all network msg
        3. Heartbeat network msg

"""
import os
import sys
import signal

_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
_TOP_PATH = os.path.abspath(_NOW_PATH + '/../../')

from cup import decorators
from cup import log
from cup import net
from cup.util import conf

from arrow.master import control
from arrow.common import settings


@decorators.Singleton
class Master(object):
    """
    Master class
    """
    _heartbeat_service = None
    _control_service = None
    _conf_dict = None
    def __init__(self, conf_file):
        # load conf
        self._load_conf(conf_file)
        # control service
        self._control_service = control.ControlService(
            net.get_hostip(), int(self._conf_dict['control']['port']),
            self._conf_dict
        )

    def _load_conf(self, conf_file):
        """
            load conf into memory.
            If user conf does not have the conf item, arrow will use
            default values in arrow.common.settings(.py)
        """
        if not os.path.exists(conf_file):
            raise IOError('conf file not found:%s' % conf_file)
        self._conf_dict = {}
        user_confdict = conf.Configure2Dict(conf_file).get_dict()
        default = settings.ARROW_MASTER_DEFAULT_PARAMS
        self._conf_dict['control'] = {}
        settings.check_and_load_existence(
            user_confdict, default, '["control"]'
        )
        self._conf_dict['control']['queue_exec_thdnum'] = \
                settings.check_and_load_existence(
            user_confdict, default, '["control"]["queue_exec_thdnum"]'
        )
        self._conf_dict['control']['queue_delay_exe_thdnum'] = \
                settings.check_and_load_existence(
            user_confdict, default, '["control"]["queue_delay_exe_thdnum"]'
        )
        self._conf_dict['control']['queue_exec_thdnum'] = \
                settings.check_and_load_existence(
            user_confdict, default, '["control"]["queue_exec_thdnum"]'
        )
        self._conf_dict['control']['local_datadir'] = \
                settings.check_and_load_existence(
            user_confdict, default, '["control"]["local_datadir"]'
        )

        self._conf_dict['control']['check_heartbeat_interval'] = \
                settings.check_and_load_existence(
            user_confdict, default, '["control"]["check_heartbeat_interval"]'
        )
        self._conf_dict['control']['judge_agent_dead_in_sec'] = \
                settings.check_and_load_existence(
            user_confdict, default, '["control"]["judge_agent_dead_in_sec"]'
        )
        self._conf_dict['control']['keep_lost'] = \
                settings.check_and_load_existence(
            user_confdict, default, '["control"]["keep_lost"]'
        )
        self._conf_dict['control']['port'] = \
                settings.check_and_load_existence(
            user_confdict, default, '["control"]["port"]'
        )

    # pylint: disable=R0201
    def setup(self):
        """setup the master"""
        log.info('master setup')

    def run(self):
        """run the master service"""
        self.setup()

    def stop(self):
        """stop the master"""

        log.info('to stop the arrow master')
        log.info('to stop control service')
        self._control_service.stop()
        log.info('arrow master stopped')

    def loop(self):
        """
        run into loop until function stop is called
        """
        pid = os.getpid()
        with open('master.pid', 'w+') as fhandle:
            fhandle.write('{0}'.format(pid))
        self._control_service.run()

    def signal_handler(self):
        """handle signals"""
        log.info('to stop control service')
        self._control_service.stop()


def signal_handler(sig, _):
    """
    signal handler for master.
    When this process receive SIGTERM signal, it will start stopping process.
    """
    if sig == signal.SIGTERM:
        log.info('get SIGTERM, to stop arrow master')
        master = Master(None)
        master.signal_handler()


def _main(argv):
    """main function"""
    log.init_comlog('arrow_master', log.INFO,
        _TOP_PATH + '/log/arrow_master.log',
        log.ROTATION,
        1024000000,
        False
    )
    signal.signal(signal.SIGTERM, signal_handler)
    if len(argv) < 2:
        sys.stderr.write('should specify conf path')
        sys.exit(-1)
    master = Master(argv[1])
    master.loop()


if __name__ == '__main__':
    _main(sys.argv)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
