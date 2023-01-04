![cuplogo](http://cup.iobusy.com/cup.logo.png)

## Notice 

- Visit http://cup.iobusy.com for more details
    - **访问 http://cup.iobusy.com 获取更多信息**
- **From now (Version 3.3.1) on, CUP will only support Python3 ** 
    - If you want use cup in Python2.7.x, plz install it with version < 3.3
        - e.g.  # python -m pip install cup==3.2.31
        - cup 3.2.X versions will only maintain bug fixes for Python2. Will not add any new features.
        - If you want to try new features, pls use cup under Python3.
    - If you use cup under Python3, pls refer to the `Installation` part.
    - 从 3.3.1 版本开始，Cup 新版本只对 Python3提供支持。如果你想继续在python2.7中使用它，请使用3.2.X版本。
    - 后续 3.2.X版本对继续提供对Python2.7的bug fix 支持，但不会再增加新的功能。
    - 推荐大家在Python3中使用Cup

## Quick Start
### 1. Download
    - git clone CUP or download the released tar balls

### 2. Installation

Install from pip

```bash
pip install cup
```

Install from source code:

```bash
python setup.py install
```

### 3. Doc & Wiki

Visit Wiki to see more details: https://github.com/Baidu/CUP/wiki

Visit Doc site to see py-docs: http://cupdoc.iobusy.com/

```python
# Examples:
# 1. Get system info
import cup
# count cpu usage in interval, by default 60 seconds
from cup.res import linux
cpuinfo = linux.get_cpu_usage(intvl_in_sec=60)
print cpuinfo.usr

# total, available, percent, used, free, active, inactive, buffers, cached
from cup.res import linux
meminfo = linux.get_meminfo()
print meminfo.total
print meminfo.available
```


## Tests
    - Install python-nose before running the tests
    - run `cd ./cup_tests; nosetests -s`

## Contribute To CUP
    - Commit code to GITHUB, https://github.com/baidu/CUP
    - Need to check pep8 and pylint rules before you start a pull request

## Discussion
    - Github Issues

## Reference
      * Pexpect http://pexpect.sourceforge.net/ (under MIT license)
      * Httplib2 http://code.google.com/p/httplib2/ (under MIT license)
      * requests https://github.com/kennethreitz/requests (under Apache V2 license)
      * pymysql https://github.com/PyMySQL/PyMySQL (under MIT license)

## WIKI
https://github.com/Baidu/CUP/wiki

## code directory tree:

```text
cup
    |-- cache.py                module              Memory cache related module
    |-- decorators.py           module              Decorators of python
    |-- err.py                  module              Exception classes for CUP
    |-- __init__.py             module              Default __init__.py
    |-- log.py                  module              CUP logging
    |-- mail.py                 module              CUP Email module (send emails)
    |-- net                     package             Network operations, such as net handler parameter tuning
    |-- oper.py                 module              Mixin operations
    |-- platforms.py            module              Cross-platform operations
    |-- res                     package             Resource usage queries (in /proc)、Process query、etc
    |-- shell                   package             Shell Operations、cross-hosts execution
    |-- services                package             Heartbeat、Threadpool based executors、file service、etc
    |-- thirdp                  package             Third-party modules： pexpect、httplib2
    |-- timeplus.py             module              Time related module
    |-- unittest.py             module              Unittest、assert、noseClass
    |-- util                    package             ThreadPool、Interruptable-Thread、Rich configuration、etc
    |-- version.py              module              CUP Version
```



## 快速开始
### 1. 下载
    - 克隆git代码或者下载已发布的tar包

### 2. 安装
    - pip 安装  `pip install cup`
    - 源码安装 `python setup.py install`

### 3. 使用说明
- Visit Wiki to see more details: https://github.com/Baidu/CUP/wiki
- Visit Doc site to see py-docs: http://cupdoc.iobusy.com/

举例说明：

```python
# Examples:
# 1. Get system info
import cup
# count cpu usage in interval, by default 60 seconds
from cup.res import linux
cpuinfo = linux.get_cpu_usage(intvl_in_sec=60)
print cpuinfo.usr

# total, available, percent, used, free, active, inactive, buffers, cached
from cup.res import linux
meminfo = linux.get_meminfo()
print meminfo.total
print meminfo.available
```


## Tests
    - Install python-nose before running the tests
    - run `cd ./cup_tests; nosetests -s`

## 向CUP贡献代码
直接在github中提交patch就可以了
    - Commit code to GITHUB, https://github.com/baidu/CUP
    - Need to check pep8 and pylint rules before you start a pull request

## Discussion
    - Github Issues

## Reference
      * Pexpect http://pexpect.sourceforge.net/ (under MIT license)
      * Httplib2 http://code.google.com/p/httplib2/ (under MIT license)
      * requests https://github.com/kennethreitz/requests (under Apache V2 license)
      * pymysql https://github.com/PyMySQL/PyMySQL (under MIT license)

## 代码树结构:

```text
cup
    |-- cache.py                module              缓存相关模块 （Memory cache related module）
    |-- decorators.py           module              python修饰符，比如@Singleton单例模式 (Decorators of python)
    |-- err.py                  module              异常exception类, Exception classes for CUP
    |-- __init__.py             module              默认__init__.py, Default __init__.py
    |-- log.py                  module              打印日志类，CUP的打印日志比较简洁、规范，设置统一、简单(cup logging module)
    |-- mail.py                 module              发送邮件 （CUP Email module (send emails)）
    |-- net                     package             网络相关操作（Network operations, such as net handler parameter tuning）
    |-- oper.py                 module              一些混杂操作(Mixin operations)
    |-- platforms.py            module              跨平台、平台相关操作函数(Cross-platform operations)
    |-- res                     package             资源获取、实时用量统计等，所有在/proc可获得的系统资源、进程、设备等信息 （Resource usage queries (in /proc)、Process query、etc）
    |-- shell                   package             命令Shell操作pakcage（Shell Operations、cross-hosts execution）
    |-- services                package             构建服务支持的类（比如心跳、线程池based执行器等等）Heartbeat、Threadpool based executors、file service、etc
    |-- thirdp                  package             第三方依赖纯Py模块（Third-party modules： pexpect、httplib2）
    |-- timeplus.py             module              时间相关的模块(Time related module)
    |-- unittest.py             module              单元测试支持模块（Unittest、assert、noseClass）
    |-- util                    package             线程池、可打断线程、语义丰富的配置文件支持（ThreadPool、Interruptable-Thread、Rich configuration、etc）
    |-- version.py              module              内部版本文件，CUP Version
```
