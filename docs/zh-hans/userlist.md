---
title: CUP 运营
tags: cup, pylib, pypi
---

[TOC]

# 1. CUP 前世今生
对于 CUP 来说, 15年末16年初是 CUP 建设的分水岭.
## 1.1 2016年前 Utilization
是建设的重点. CUP 起源于对如下内容的 a. 标准化处理 b. 减少重复造轮子
1. 减少重复造轮子:
    - 配置文件 cup.util.conf
        - 与c/c++ comcfg/configure库100%兼容
        - 支持将 configure 库映射为py dict, 以及pydict 回写到文件
    - 可打断线程 cup.thread
    - 发短信/回邮件/查noah cup.bidu
    - 等等

2. 标准化
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
- 适度宣传

在16年初, CUP 已没有了最初紧迫的生存压力, 转而考虑一个长期建设的基础库的样子.

## 1.2 2016至今 Service
在经过了半年左右的考察和决策(其实主要是犹豫不定,可做的范围很大,但总要有一定的取舍).
CUP 定位后续发展主要为构建一个Python Serivce服务.

打个比方, 构建一个Python Service是 CUP 这个技术栈的主干, 前期的 Util 相关功能实现都是这个主干上的枝叶.
> CUP 团队以构建一个分布式服务为模型作为理想的基础库技术栈:
>
>   - 其实并不存在完全理想的技术栈, 团队选择构建一个分布式服务主要是核心开发人员的技术背景导致的
>       - 开发人员以分布式存储系统、分布式trace/监控等系统出身为主
>       -
>   - 分布式服务一般会囊括服务的各个方面, 从底层的网络通信、线程池、数据存储到中间的配置文件等覆盖面较广
>       - 发展空间比较广阔
>       - 典型的分布式服务也是基础库的试金石, 才能保证库的稳定\\高质量发展

# 2. 已支持的服务

## 2.1 支持的平台服务
- 专有云Dailybuild
- 公有云TCP
- 负载测试框架Arrow
- 公有云版本服务
- 异常服务、DIFI1.0、DIFI2.0
- 公有云背景压力
- 私有云联测平台
	- 线上监控和预警
	- Preonline平台
- DevOps 平台 XSTP/XTS
- 联盟分发app平台
- 网盟线下测试服务 bts

## 2.2 支持的项目
支持100+个项目|Topic测试（16年后不在进行费时统计）

举例说明:

- 基础技术测试部
    - NFS、AFS、TableII、EBS、EVM、object、DT_UT、Wing、Billing、console、erp、hi、monitor、sysqa-uuap、BAE
- 移动云测试部
    - 云安全监控
- Ecomqa
    - csqa、XTS、压测平台、IMQA
- PSQA
    - 站长平台
- 其他类:
    - Good-coder

![userlist_0.png](images/userlist_0.png)
![userlist_1.png](images/userlist_1.png)
![userlist_2.png](images/userlist_2.png)
