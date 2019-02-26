## 介绍
- CUP 基础库是百度开源的 Python 语言基础库，致力将 Python Developer 从涉及底层操作、Util操作解放出来，更关注构建 service 上层业务逻辑。
- 目前已涵盖了构建一个服务的各个方面，大家可以从基础库的代码结构、wiki、doc 中进行简单了解。

```text
cup
    |-- cache.py                module              缓存相关模块 （ Memory cache related module ）
    |-- decorators.py           module              python 修饰符，比如 @Singleton 单例模式 (Decorators of python)
    |-- err.py                  module              异常 exception 类, Exception classes for CUP
    |-- __init__.py             module              默认__init__.py, Default __init__.py
    |-- log.py                  module              打印日志类，CUP 的打印日志比较简洁、规范，设置统一、简单(cup logging module)
    |-- mail.py                 module              发送邮件 （ CUP Email module (send emails)）
    |-- net                     package             网络相关操作（ Network operations, such as net handler parameter tuning ）
    |-- oper.py                 module              一些混杂操作(Mixin operations)
    |-- platforms.py            module              跨平台、平台相关操作函数(Cross-platform operations)
    |-- res                     package             资源获取、实时用量统计等，所有在 /prco 可获得的系统资源、进程、设备等信息 （ Resource usage queries (in /proc)、Prcoess query、etc ）
    |-- shell                   package             命令 Shell 操作 pakcage （ Shell Operations、cross-hosts execution ）
    |-- services                package             构建服务支持的类（比如心跳、线程池 based 执行器等等） Heartbeat、Threadpool based executors、file service、etc
    |-- thirdp                  package             第三方依赖纯 Py 模块（ Third-party modules：pexpect、httplib2 ）
    |-- timeplus.py             module              时间相关的模块(Time related module)
    |-- unittest.py             module              单元测试支持模块（ Unittest、assert、noseClass ）
    |-- util                    package             线程池、可打断线程、语义丰富的配置文件支持（ ThreadPool、Interruptable-Thread、Rich configuration、etc ）
    |-- version.py              module              内部版本文件，CUP Version
```


如果你觉得 CUP 很棒，请帮我们 star，并推荐给厂内、厂外的 亲朋砖友。
更欢迎为 CUP 撰写 patch、新 feature，一起添砖加瓦！

- Github:  https://github.com/Baidu/CUP
- Wiki:  https://github.com/baidu/CUP/wiki
- Doc: http://cupdoc.iobusy.com

感谢， ---Gallon