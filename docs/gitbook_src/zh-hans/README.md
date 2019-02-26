# CUP介绍
<!-- MDTOC maxdepth:6 firsth1:1 numbering:0 flatten:0 bullets:1 updateOnSave:1 -->

- [CUP介绍](#CUP介绍)
   - [1. 下载](#1-下载)
   - [2. 安装](#2-安装)
   - [3. 问题反馈](#3-问题反馈)
   - [4. 致  敬 (Pay Tribute To)](#4-致-敬-Pay-Tribute-To)
   - [5. 发展历程](#5-发展历程)
   - [6. 用户案例](#6-用户案例)
      - [6.1 典型用户案例](#61-典型用户案例)

<!-- /MDTOC -->

**1分钟了解Python-Cup基础库**
<iframe src="//player.bilibili.com/player.html?aid=41856081" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" width="900px" height="900px"> </iframe>

----------

如果你觉得 CUP 很棒，请帮我们 star https://github.com/baidu/CUP
，并推荐给亲朋砖友.

更欢迎为 CUP 撰写 patch、新 feature，一起添砖加瓦！


## 1. 下载
- git clone CUP or download the released tar balls
  - https://github.com/baidu/CUP

## 2. 安装
- run bash cmd to install
```bash
python setup.py install
```
- pip 安装
    - pip安装依赖pypi社区批准cup替换原有的cup lib. 
    - 当前功能已 ready, 还在等待pypi社区审批

## 3. 问题反馈
- Open Github Issues

## 4. 致  敬 (Pay Tribute To)
CUP中直接或间接使用了如下module, 向以下社区项目致敬:
* Pexpect http://pexpect.sourceforge.net/ (under MIT license)
* Httplib2 http://code.google.com/p/httplib2/ (under MIT license)
* requests https://github.com/kennethreitz/requests (under Apache V2 license)
* pymysql https://github.com/PyMySQL/PyMySQL (under MIT license)


## 5. 发展历程

对 CUP 来说, 15年末16年初是 CUP 建设的分水岭.


**2016年前Cup初创阶段Utilization是建设的重点.**
CUP初衷并不复杂， 就是朴素的目标： `降低人力`。

当时的背景是，
- 我们的观察，Python作为胶水语言，编码上手特别容易，实现方式也比较灵活，少量代码可以构建大的场景，这是她的优点。
- 但应用过程中灵活性也与冗余代码、混乱无序的实现方式伴生。短时间快速实现欠得技术债总会在后面某个时段爆发，而且带来的人力消耗和时间成本overweigh前面抢得那一点时间。

于是把常用的场景抽象出来， `标准化`并`减少重复造轮子`成为我们最好的选择. 举例来说：

- 减少重复造轮子
    - 配置文件 cup.util.conf
        - 与c/c++ comcfg/configure库100%兼容
        - 支持将 configure 库映射为py dict, 以及pydict 回写到文件
    - 可打断线程 cup.thread
    - 发短信/回邮件/查noah cup.bidu
    - 等等

- 标准化
    - 日志标准化打印 cup.log
        - 参考文章[Optimal logging](http://blog.iobusy.com/%E7%9F%A5%E8%AF%86%E7%A7%AF%E7%B4%AF/optimal-logging/)
    - Shell 执行标准化 cup.shell
        - timeout 超时处理标准化
        - 回返信息处理标准化
        - expect(exe & scp系列)处理标准化
    - 等等

随着时间推移, 使用 CUP 的项目越来越多(超过50+). 原因来说无外乎三个:
- 质量尚佳
- 文档齐全
- 持续交付

16年初, CUP 已没有最初紧迫的生存压力(是否可以扎根生长), 转而考虑一个长期建设基础库的样子.

-----

**2016至今, CUP 目标: 为快速构建Python Serivce提供服务**.

在经过了半年左右的考察和决策(主要是犹豫不定,可做的范围很大. 但总要有取舍和收敛)，我们确定了支持构建Python Service的长期稳定目标。
- 长期代表该目标会持续交付
- 稳定代表不会随便动摇， 不会随着新兴的技术诉求涌现而混淆核心目标。弱水三千，只取一瓢，才能饮尽。


## 6. 用户案例 ##

### 6.1 典型用户案例
- 快速使用cup开开发python程序，可查看两类文档
  - [常用lib库支持场景](./senarios/CommonUserSenario.md)
  - [官方API文档](http://cup.iobusy.com/api)
- 使用CUP如何构建一个Service， 欢迎查看
  - [Cup Service篇](senarios/GeneralService.md).
