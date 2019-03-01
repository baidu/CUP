<!-- MDTOC maxdepth:6 firsth1:1 numbering:0 flatten:0 bullets:1 updateOnSave:1 -->

- [1. 常用操作](#1-常用操作)
   - [1.1 cup.mail 发送邮件类](#11-cupmail-发送邮件类)
   - [1.2 cup.log 简单好用的cup log函数](#12-cuplog-简单好用的cup-log函数)
   - [1.3 cup.res 获取linux机器资源类相关信息](#13-cupres-获取linux机器资源类相关信息)
   - [1.4 cup.shell 操作shell命令相关的package.](#14-cupshell-操作shell命令相关的package)
   - [1.5 cup.util util类package - Rich Configuration/Context](#15-cuputil-util类package-Rich-ConfigurationContext)
   - [1.6 cup.net 网络操作相关的package.](#16-cupnet-网络操作相关的package)
      - [1.6.1 网卡信息获取、路由信息获取、socket设置](#161-网卡信息获取路由信息获取socket设置)
      - [1.6.2 异步网络消息通信库](#162-异步网络消息通信库)
   - [1.7 cup.decorators 进行函数、类修饰的module](#17-cupdecorators-进行函数类修饰的module)
   - [1.8 cup.jenkinslib 与持续集成平台进行API操作](#18-cupjenkinslib-与持续集成平台进行API操作)
   - [1.9 cup.exfile](#19-cupexfile)
   - [1.10 cup.thirdp 第三方的库依赖支持](#110-cupthirdp-第三方的库依赖支持)

<!-- /MDTOC -->


# 1. 常用操作

目前基础库包含如下大的Package[每类包含若干小的package及module].

___排序按照常用->较常用->专用___

## 1.1 cup.mail 发送邮件类

具体文档介绍

> http://cupdoc.iobusy.com/cup/#module-cup.mail

代码示例：
```python
from cup import mail
mailer = mail.SmtpMailer(
    'xxx@xxx.com',   # sender
    'xxxx.smtp.xxx.com',  # smtp server
    is_html=True   # use html or not for email contents
)
mailer.sendmail(
    [
        'abc@baidu.com',
        'xxx@baidu.com',
        'yyy@baidu.com'
    ],
    'test_img',
    (
        'testset <img src="cid:screenshot.png"></img>'
    ),
    # attachment
    [
        '/home/work/screenshot.png',
        '../abc.zip'
    ]
)
```

## 1.2 cup.log 简单好用的cup log函数
> 去除复杂log设置，即开即用

 具体文档介绍

> http://cupdoc.iobusy.com/cup/#module-cup.log

 代码示例：

```python
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
log.error('test critical')

# 支持重新设置日志level、日志文件位置、参数等，具体参数设置见文档
```
```python

# Level: Datetime * [pid:threadid] [source.code:lineno] content
INFO:    2017-02-06 19:35:54,242 * [16561:140543940048640] [log.py:278] --------------------Log Initialized Successfully--------------------
INFO:    2017-02-06 19:35:54,242 * [16561:140543940048640] [cup_log_test.py:36] info
DEBUG:   2017-02-06 19:35:54,243 * [16561:140543940048640] [cup_log_test.py:40] debug
```

## 1.3 cup.res 获取linux机器资源类相关信息
举例， 获得当前机器cpu/mem/net统计信息。 进程资源信息（所有/proc/pid能拿到的资源信息)
 具体文档介绍

> http://cupdoc.iobusy.com/cup.res/

 代码示例：

```python
# 1. 获取系统信息， 可以获取cpu mem network_speed等等
import cup
# 计算60内cpu的使用情况。
from cup.res import linux
cpuinfo = linux.get_cpu_usage(intvl_in_sec=60)
print cpuinfo.usr

# get_meminfo函数取得系统Mem信息的回返信息。 是个namedtuple
# total, available, percent, used, free, active, inactive, buffers, cached是她的属性

from cup.res import linux
meminfo = linux.get_meminfo()
print meminfo.total
print meminfo.available

# 获取系统其他信息， 如启动时间、cpu情况、网卡情况等
cup.res.linux.get_boottime_since_epoch()# Returns:	回返自从epoch以来的时间。 以秒记.
cup.res.linux.get_cpu_nums()[source] # 回返机器的CPU个数信息
cup.res.linux.get_disk_usage_all() # 拿到/目录的使用信息， 回返是一个字典
cup.res.linux.get_disk_info() # 拿到Linux系统的所有磁盘信息

cup.res.linux.get_cpu_usage(intvl_in_sec=1) # 取得下个intvl_in_sec时间内的CPU使用率信息 回返CPUInfo

cup.res.linux.get_kernel_version() # 拿到Linux系统的kernel信息， 回返是一个三元组 e.g.(‘2’, ‘6’, ‘32’):

cup.res.linux.get_meminfo() # 获得当前系统的内存信息， 回返MemInfo数据结构。

cup.res.linux.get_net_recv_speed(str_interface, intvl_in_sec) # 获得某个网卡在intvl_in_sec时间内的收包速度

cup.res.linux.get_net_through(str_interface) # 获取网卡的收发包的统计信息。 回返结果为(rx_bytes, tx_bytes)

cup.res.linux.get_net_transmit_speed(str_interface, intvl_in_sec=1) # 获得网卡在intvl_in_sec时间内的网络发包速度

print cup.res.linux.get_net_transmit_speed('eth1', 5)

cup.res.linux.get_swapinfo() # 获得当前系统的swap信息

cup.res.linux.net_io_counters() # net io encounters
```

```python

# 2. 获取进程相关信息， 移植自psutil，可以获取/proc/xxxpid进程内的所有信息
# 也可以获取该进程下所有子进程相关的信息, 详见代码
get_connections(*args, **kwargs)

get_cpu_times(*args, **kwargs)

get_ext_memory_info(*args, **kwargs)

get_memory_info(*args, **kwargs)

get_memory_maps()

get_num_ctx_switches(*args, **kwargs)[source]

get_num_fds(*args, **kwargs)[source]

get_open_files(*args, **kwargs)[source]

get_process_cmdline(*args, **kwargs)[source]

get_process_create_time(*args, **kwargs)[source]

get_process_cwd(*args, **kwargs)[source]

get_process_exe()[source]
获得进程的Exe信息。 如果这个进程是个daemon，请使用get_process_name

get_process_gids(*args, **kwargs)[source]

get_process_io_counters(*args, **kwargs)[source]

get_process_name(*args, **kwargs)[source]

get_process_nice(*args, **kwargs)[source]

get_process_num_threads(*args, **kwargs)[source]

get_process_ppid(*args, **kwargs)[source]

get_process_status(*args, **kwargs)[source]

get_process_threads(*args, **kwargs)[source]

get_process_uids(*args, **kwargs)[source]

nt_mmap_ext alias of mmap

nt_mmap_grouped alias of mmap
```


## 1.4 cup.shell 操作shell命令相关的package.
**任何shell操作都应该考虑超时机制!!!**
> 否则可能导致某单个shell cmd 执行 hang 住, 整个线程/进程卡住.
> shell.ShellExec类就是为了该理念而设计, 支持超时auto-kill操作

 具体文档介绍

> http://cupdoc.iobusy.com/cup.shell/

  代码示例
```python
# 特色示例
# 1. 拥有超时控制的shell执行. 超时shell命令会被kill (SIGTERM)
import cup
shelltool = cup.shell.ShellExec()
print shelltool.run('/bin/ls', timeout=1)

# 2. 其他类，比如使用rm -rf删除某路径，获取文件MD5等
cup.shell.md5file(filename) # 计算一个文件的md5值。返回32位长的hex字符串。

cup.shell.kill9_byname(strname) # kill -9 process by name

cup.shell.del_if_exist(path) # 如果文件/目录/symlink存在则删除他们

# 3. 进行远程shell操作 （内部调用了pexpect)

# 具体参照 http://cupdoc.iobusy.com/cup.shell/#module-cup.shell.expect
# 其中exit_status为本地ssh命令退出码， remote_status为远程的退出码
```

## 1.5 cup.util util类package - Rich Configuration/Context

> 各类util类pacakge
> - 富配置类型, 参见下面介绍
> - 线程上下文

 具体文档介绍

> http://cupdoc.iobusy.com/cup.util/  总览

```python

#1 支持类型丰富、带内嵌套、数组的文档 http://cupdoc.iobusy.com/cup.util/#cup.util.conf.Configure2Dict
# test.conf
# 第一层，Global layer, key:value
host: abc.com
port: 12345
# 1st layer [monitor]
@disk: sda
@disk: sdb

# 第二层配置 conf_dict['section']
[section]
    # 支持数组 conf_dict['section']['disk'] =>是个一维数组
    @disk: sda
    @disk: sdb
    # 支持层级数组  conf_dict['section']['ioutil'] => 是个一维数组
    [@ioutil]
        util: 80   # accessed by conf_dict['section']['ioutil'][0]['util']
    [@ioutil]
        util: 60


[monitor]
    timeout: 100
    regex:  sshd
    # 2nd layer that belongs to [monitor]
    # 第三层配置  conf_dict['monitor']['timeout']
    [.timeout]
        # key:value in timeout
        max: 100
        # 3rd layer that belongs to [monitor] [timeout]
        [..handler]
            default: exit


# 3. 生成唯一码、唯一数等
# http://cupdoc.iobusy.com/cup.services/#module-cup.services.generator
```

## 1.6 cup.net 网络操作相关的package.

> 两个重要部分：

* a. 网卡信息获取、路由信息获取、socket参数设置
* b. 异步消息通信协议支持

 ### 1.6.1 网卡信息获取、路由信息获取、socket设置

 具体文档介绍

> http://cupdoc.iobusy.com/cup.net/

 代码示例：


```python
# 1. 获取路由信息
from cup.net import route
ri = route.RouteInfo()
print json.dumps(ri.get_route_by_ip('10.32.19.92'), indent=1)
print json.dumps(ri.get_routes(), indent=1)

{
 "Use": "0",
 "Iface": "eth1",
 "Metric": "0",
 "Destination": "10.0.0.0",
 "Mask": "255.0.0.0",
 "RefCnt": "0",
 "MTU": "0",
 "Window": "0",
 "Gateway": "10.226.71.1",
 "Flags": "0003",
 "IRTT": "0"
}
[
 {
  "Use": "0",
  "Iface": "eth1",
  "Metric": "0",
  "Destination": "10.226.71.0",
  "Mask": "255.255.255.0",
  "RefCnt": "0",
  "MTU": "0",
  "Window": "0",
  "Gateway": "0.0.0.0",
  "Flags": "0001",
  "IRTT": "0"
 },

# 2. 获取ip && 设置socket参数等
from cup import net

# set up socket params
net.set_sock_keepalive_linux(sock, 1, 3, 3)
net.set_sock_linger(sock)
net.set_sock_quickack(sock)
net.set_sock_reusable(sock, True)  # port resuable

# get ipaddr of a network adapter/interface
print net.getip_byinterface('eth0')
print net.getip_byinterface('eth1')
print net.getip_byinterface('xgbe0')   # 万兆网卡

# get ipaddr of a hostname
print net.get_hostip('abc.test.com')

```

### 1.6.2 异步网络消息通信库

 具体文档介绍

> http://cupdoc.iobusy.com/cup.net.async/#module-cup.net.async.msgcenter

 具体介绍：
 - 请移步左侧关于网络通信协议介绍

异步消息库属于专用且较为复杂的通信库，为高吞吐、高效网络通信场景使用，请注意你的使用场景是否匹配


## 1.7 cup.decorators 进行函数、类修饰的module

举例，一键变类为Singleton类。


## 1.8 cup.jenkinslib 与持续集成平台进行API操作

 代码示例：

```python
import cup
import cup.jenkinslib

############### quick start ###############
jenkins = cup.jenkinslib.Jenkins('cup.jenkins.baidu.com')

job = jenkins['cup_quick']
print job.name, job.last_stable_build_number, job.description
print job[5], job["lastSuccessBuild"], job.last_stable_build

qi = job.invoke()
build = qi.block_until_building()
print build.name, build.number, build.timestamp

try:
    build.block_until_complete(timeout=20)
except cup.jenkinslib.RunTimeout as err:
    print "timeout:", err
    build.stop()

print build.duration, build.result, build.description

build.description = "new description"

jenkins.enable_ftp('ftp.baidu.com', 'cup', 'password', 22)
with build.ftp_artifacts as af:
    af['artifacts_path'].download('./local_path')

```
## 1.9 cup.exfile
exfile 代表extension of file related objects. 目前支持:
- LockFile, 独占式锁文件
- TempFile，临时文件，在生命周期到期后自动删除

a. LockFile代码示例：

```python
def test_sharedlockfile():
    """test lockfile"""
    # shared lockfile
    _lockfile = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_SHARED)
    ret = _lockfile.lock(blocking=False)
    print ret
    _lockfile2 = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_SHARED)
    ret = _lockfile2.lock(blocking=False)
    print ret
    _lockfile3 = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_EXCLUSIVE)
    unittest.expect_raise(
        _lockfile3.lock,
        err.LockFileError,
        False
    )

def test_exclusive_lockfile():
    """test exclusive lockfile"""
    # shared lockfile
    _lockfile = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_EXCLUSIVE)
    _lockfile.lock()
    _lockfile2 = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_EXCLUSIVE)
    unittest.expect_raise(
        _lockfile2.lock,
        err.LockFileError,
        blocking=False
    )
    _lockfile3 = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_SHARED)
    unittest.expect_raise(
        _lockfile3.lock,
        err.LockFileError,
        blocking=False
    )
```

b. TempFile示例
```python
# 请注意在tmp变量生命周期结束后， 该temp文件会被立刻删除
def test_func():
    tmp = exfile.TempFile()
    tmp.write/read/etc
    tmp.close()
```

## 1.10 cup.thirdp 第三方的库依赖支持
- httplib2
- requests
- MySQLdb (pymysql inside)
- pexpect
