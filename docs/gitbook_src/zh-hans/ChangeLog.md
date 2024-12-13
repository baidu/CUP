# 0. Version Under Development

## Version 3.2.34

* cup.services.generator
  * [new] replace CGeneratorMan with new class Py3Generator
  * [compatibility] cup.servcies.generator, unicode<>str in py3/py2
  * [enhancement] 
* cup.timeplus
  * [new] add timestamp2datetime for converting timestamp to datetime object
* cup.cache
  * [new] add mapupdate function for KVMemCache
  * [bug] fix bug for KVMemCache.expire
* cup.mail
  * [enhancement] add Smtp with ssl support
* cup.storage.obj s3 object apis
  * [new] Add ssl verify support with local public crt file
  * [enhancement] Change open mode from unspecified to binary mode. r -> rb; w+ -> wb

# 1. Versions Released

## Version 3.2.27

* [Dependence Change] Remove pymysql
* [New] cup.net.asyn | supports kqueue on mac
* [New] cup.res.mac | supports MacResource based on psutil
* [New] cup.services.heartbeat supports MacHost

## Version 3.2.26

* [Bug] Epoll Lost Events Bug fix
* [Compatibility] Fix Py2 comatibility issue for cup.services.heartbeat

## Version 3.2.20

* [Compatibility] *cup.log* | Fix unicode bug for py3
* [Enhancement] *cup.log* | Add xdebug/xinfo/xinit_comlog in order to support different loggers
* [Removal] *cup.jenkinslib* | Recommand using python-jenkins to replace cup.jenkinslib
* [Enhancement] *cup.cache*| Enhance KVCache, add pop_expired. Support setting up "maxsize" for the cache pool
* [Enhancement] *cup.services.buffer*| Fix encode/decode bug for py3

## Version 3.2.19

* [Enhancement] *cup.services.generator* | Add visibility to Cached UUID
* [Enhancement] *cup.util.conf* |  Fix py3 support bug
* [New] *cup.services.executor* | Add Crontab-like execution service
* [Bug] *cup.net.asyn.context* | Fix bug which introduces RW Lock problem
* [Compatibility] * cup.shell.expect | Fix compatibility bug related to remote execution
* [New] *cup.timeplus* | Add TimePlus for i18n time related functions
* [Bug] *cup.shell.oper and cup.shell.expect* | Fix bugs for remote execution and async shell run

## Version 3.2.7  2020.1.1 ~ 2020.3.31

* [Enhancement] Change cup.net.async to cup.net.asyn to avoid language keyword "async"
* [New] Support Python version >= 3.5
* [New] add safe_rmtree in cup.exfile
* [Bug] *cup.exfile* fix bug for cup.exfile for macos
* [Bug] *cup.shell.ShellExec* fix bug for 
* [New] Add support for global socket keepalive
* [Enhancement] *cup.exfile* Add some path into CANNOT_DEL_PATHLIST
* [New] *cup.services.generator* Add cached generator 
* [Enhancement] *cup.shell.expect* Replace shell expect with paramiko based remote cmd execution
* [Enhancement] *cup.net.async.conn* Replace mutex lock with ReadWriteLock to speed up 

## Version 3.1.x Under Development 2019.9 ~ 2019.12.26

* [Enhancement] cup.services.serilizer - loglist
* [New] cup.storage.obj - rename
* [Bug] cup.storage.obj - ftp uri bug

## Version 3.0.0 py support alpha 2019.6 ~ 2019.8.8

* [Enhancement] cup.net get ip address
* [New] Py3 support (excep for cup.net.async, tcp async msg stack)
* [Bug] fix traceback for cup.storage.obj 
* [Enhancement] cup.exfile - support lock_file for windows
* [Bug] Fix installation bug in setup.py
* [New] Add get unique hexid for cup.services.generator

## Version 2.2.0 - 2019.5.11 ~ 5.29

* [Fancy] Change a new logo, hats to community user @davidmind (from github) 
* [New] `cup.res` - linux.Process add method `getpgid`
* [New] add BceSms support
* [Enhancement] `cup.shell` - enhance `oper.ShellExec`
* [Enhancement] `cup.mail` - add smtp login method for authentication enabled server

## Version 2.1.0 - 2019.2.1 ~ 2019.5.10

    * [New] cup.net.get_interfaces - Get interfaces of a linux host
    * [New] cup.res.linux.get_cpu_core_usage - Get cpu core usage 
    * [Enhancement] cup.shell.oper - Md5 hexdigest generation (py3 compatibility)
    * [New] Py3 compatibility test and reconsutrction is undergoing
    * [Enhancement] cup.shell.oper - Change subprocess.Pipe(shell=True by default to shell=False)
    * [Bug] github socket closure (https://github.com/baidu/CUP/issues/32) 
    * [Bug] cup.shell.oper async_run, kill procedure for children pids has bugs 

## Version 2.0.0 - 2018.6.2 ~ 2018.12.31

* [New] pip support
* [New] cup.storage.obj - Add ftp/s3/local storage support (with universal apis)
* [Bug] cup.net.localport_free - Reversely result returned
* [Bug] cup.net.async - Msg class class variable 
* [Bug] cup.net.async - logging typo
* [Bug] cup.net.async - Msg disorder bug (an import bug fix!)
* [New] cup.net.async - Add get_context related class method
* [Bug] cup.decorators - fix wrap exception
* [Bug] cup.unittest - Fix bug for assert_lt
* [Bug] cup.res.linux - Add support for customized linux kernel
* [Enahcnement] cup.net.set_sock_keepalive_linux - add exception catch code lines
* [Enhancement] Use rtd (read_the_doc theme) to reconsutrct cup api-doc

## Version 1.6.1 - starting from 2018.2.5 ~ 2018.6.1

* [New] cup.shell.is_proc_alive - Add optional to abandon vim|less|vi|tail|cat|more or custom filter	
* [Bug] cup.shell.get_pid - Fix grep to surely abandon vim|less|vi|tail|cat|more 
* [New] cup.log - Add support for stack manipulation, which can pop out function calls.
* [New] cup.err - Add UnImplemented exception class.
* [New] cup.exfile - Support temp files which will be removed immediately after the variable life ends.
* [Enhancement] cup.util.conf - support $ in a conf key
* [Doc] cup.shell - Fix doc bug. 
* [New] cup.shell - Add grep support string with space
* [New] cup.storage.obj - Support common object storage apis including ftp, s3
* [Bug] cup.res.linux - Getting cpuinfo has bugs (new kernel 3.10)
* [Enhancement] - cup.util.threadpool, add daemon_threads as the parameter
    that you can use to let the threadpool threads behave like daemon-thread
    (when the main thread exits, it exits as well)
* [Enhancement] - conf.util.conf - support conf line "[.test] # comments" 

## Version 1.6.0 - starting from 2017.9.6 ~ 2017.12.29

  * [New] cup.bidu.icafe - interact with baidu icafe.
  * [New] MsgBroker - Add a broker for handling system failures
  * [New] cup.
  * [Bug] Linux Resource Query Bug - related to data columuns
  * [Bug] cup.net.async - socket cannot be got.
  * [Enhancement] cup.net.async - CUP utilization enhancement

## Version 1.5.6 - starting from  2017.3.1 ~ 2017.9.5

  * [Enhancement] async enhancement for stability
  * [New] CycleIDGenerator for generating universally unique_id (ip, port
    encoded as part of the id)
  * [Enhancement] cup.net.async exits more quickly than before
  * [Bug] cup.net.async - Fix CPU-utilization too high bug
  * [Bug] cup.net.async - Fix getting-peerinfo bug
  * [Bug] cup.res.linux - Kernel version was returned with a tuple
    ('2', '6', '32') which should be (2, 6, 32)

## Version: 1.5.5 - staring from 11.18 ~ 2017.3.1

  * [Enhancement] debug method for executor
  * [async] CNeedAckMsg & retry mechnism added. CAckMsg added

## Version: 1.5.4 - Starting from 2016.9 ~ 2016.11.11

  * [Enhancement] generator supports staring point
  * [Enhancement] catch exception socket.gaierror when it encounters network
    instability
  * [Bug] Set up splitter other thant colon in a Configure2Dict with blanks and comments 
  * [Async] Support automatic msg retry
  * [Async] Support ack msg

## Version: 1.5.3 - Starting from 2016.6 to 2016.8

  * [New] cup.util.conf - support $include "conf_file" syntax [write/read]
  * [New] port free check. Listened port probe.
  * [Enhancement] cup.net.async - enhance network write/read speed. 
    Example provided
  * [Improvement] - Improve cup.log performance
  * [Enhancement] cup.util.threadpool, callback function will receive
    Exception object (param result) if it encounters error.

## Version: 1.5.1 && 1.5.2

  * [New] cup.log - add xxx_if 
  * [New] cup.thirdp - replace MySQLdb with pymysql. 
    * from cup.thirdp import pymysql
    * import MySQLdb
  * [New] cup.util.generator - get_random_str
  * [Bug] cup.util.conf - bug fix

## Version: 1.5.0

  * [New] cup.jenkinslib - add jenkins lib with which you can operate on jenkins jobs
  * [New] cup.log.parse - parse string line logged by cup.log.XXX
  * [New] cup.unittest.assert_startswith
  * [New] cup.oper - add contains_file which searchs a file and return its existence
  * [Bug] cup.util.conf - fix "key comparation order" bug for Configure2Dict
  * [Bug] cup.util.conf - fix HdfsXmlConf "eletemnt without value. e.g. <value/>

## Version: 1.4.2

  * [Bug] oper.is_proc_exist. fix a bug while check proc exist
  * [New] Add cup.services.executor. Exec and delay_exec service
  * [New] Add cup.services.buffers. Buffer releated feature. For easing
        memory fragment.	
  * [Enahcnement] remove traceback in cup.util.threadpool
  * [Enhancement] cup.log.reinit_comlog, if loggername has inited, raise
  ValueError
    * [New]  cup.log.get_inited_loggername, get has inited loggername
  * [New]  cup.shell.rmtree - add safemode support for shutil.rmtree
  * [New]  cup.const - add const value support inside cup
  * [New]  cup.conf - add HdfsConf support
  * [New]  cup.shell.get_pid - get process id by process_path and grep_string

## Version: 1.4.1

  * [New] assert_boundary, assert_local_file_eq 2015/4/19
  * [New] Log level [warnning error fatal] splitted into file.log.wf
  * [New] Hdfs
  * [New] Smtp mail supports [cc/bcc]
  * [Enhancement] Sms add return values
  * [Bug] cup.util.conf - A sort method bug
  * [Bug] sms cannot handle \n as line separator
  
## Version: 1.2.0

 - unittest  
  * [New] Add assert_not_eq
 - decorators Add 
  * [New] Add TraceUsedTime. For tracing used time in a function
  * [Bug] Bug decorators.Singleton (May cause a thread hang)
 - cup.bidu
  * fix a bug which will block cup usage on windows
  * add jenkins support
