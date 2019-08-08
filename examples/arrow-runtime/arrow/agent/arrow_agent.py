#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
:authors:
    Guannan Ma @mythmgn
:create_date:
    2016/05/05
:modify_date:

:description:

"""
import os
import sys
import signal

from cup import decorators
from cup import net
from cup.util import conf
from cup import log

from arrow.agent import control
from arrow.common import settings


_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
_TOP_PATH = os.path.abspath(_NOW_PATH + '/../../')


@decorators.Singleton
class Agent(object):
    """
    Class of Agent.
    """
    _heartbeat_sender = None
    _control_service = None
    _conf_dict = None
    def __init__(self, conf_file):
        # load conf
        self._load_conf(conf_file)
        # control service
        ipaddr = net.get_hostip()
        port = int(self._conf_dict['control']['port'])
        # control service which control msg sending and receiving.
        self._control_service = control.ControlService(
            ipaddr, port, self._conf_dict
        )
        log.info('ip:{0}, port:{1}'.format(ipaddr, port))
        self._stop_heart_beat = False

    def _should_stop_heartbeat(self):
        return self._stop_heart_beat

    def _load_conf(self, conf_file):
        """load agent conf"""
        if not os.path.exists(conf_file):
            raise IOError('conf file not found:%s' % conf_file)
        self._conf_dict = {}
        user_confdict = conf.Configure2Dict(conf_file).get_dict()
        default = settings.ARROW_MASTER_DEFAULT_PARAMS
        control_conf = {}
        log_conf = {}
        control_conf['heartbeat_interval'] = settings.check_and_load_existence(
            user_confdict, default, '["control"]["heartbeat_interval"]'
        )
        control_conf['master_ip'] = settings.check_and_load_existence(
            user_confdict, default, '["control"]["master_ip"]'
        )
        control_conf['master_port'] = settings.check_and_load_existence(
            user_confdict, default, '["control"]["master_port"]'
        )
        control_conf['queue_exec_thdnum'] = settings.check_and_load_existence(
            user_confdict, default, '["control"]["queue_exec_thdnum"]'
        )
        control_conf['queue_delay_exe_thdnum'] = settings.check_and_load_existence(
            user_confdict, default, '["control"]["queue_delay_exe_thdnum"]'
        )
        control_conf['port'] = settings.check_and_load_existence(
            user_confdict, default, '["control"]["port"]'
        )
        control_conf['interface'] = settings.check_and_load_existence(
            user_confdict, default, '["control"]["interface"]'
        )


        log_conf = settings.check_and_load_existence(
            user_confdict, default, '["log"]["path"]'
        )
        self._conf_dict['control'] = control_conf
        self._conf_dict['log'] = log_conf

    # pylint: disable=R0201
    def setup(self):
        """setup the master"""
        log.info('agent setup')

    def stop(self):
        """stop the master"""

    def loop(self):
        """
        run into loop until function stop is called.
        """
        self._control_service.loop()

    def signal_handler(self):
        """handle signals"""
        self._control_service.stop()


def signal_handler(sig, _):
    """
    signal handler for master.
    When this process receive SIGTERM signal, it will start stopping process.
    """
    if sig == signal.SIGTERM:
        log.info('get SIGTERM, to stop arrow master')
        agent = Agent(None)
        agent.signal_handler()


def _main(argv):
    """main function"""
    log.init_comlog('arrow_master', log.INFO,
        _TOP_PATH + '/log/arrow_agent.log',
        log.ROTATION,
        1024000000,
        False
    )
    signal.signal(signal.SIGTERM, signal_handler)
    if len(argv) < 2:
        sys.stderr.write('should specify conf path')
        sys.exit(-1)
    agent = Agent(argv[1])
    agent.loop()


if __name__ == '__main__':
    _main(sys.argv)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
