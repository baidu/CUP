#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################

"""
:author:
    Guannan Ma
:create_date:
    2014
:last_date:
    2014
:descrition:
    mail related modules. **Recommand using SmtpMailer**
"""

__all__ = ['mutt_sendmail', 'SmtpMailer']

import os
import warnings
import mimetypes
import smtplib
from email.mime import multipart
from email import encoders
from email.mime import audio
from email.mime import base
from email.mime import image
from email.mime import text

import cup
from cup import log


def mutt_sendmail(  # pylint: disable=R0913,W0613
    tostr, subject, body, attach, content_is_html=False
):
    """
    请注意。mutt_sendmail不推荐被使用，除非无法使用此module的SmtpMailer.

    :param  exec_cwd:
        切换到exec_cwd目录，然后发送邮件。 发送之后会回到原来的workdir.
        如果不期望切换目录， 请传入''
    :param tostr:
        收件人列表， 可多人。 用,分隔
    :param subject:
        邮件主题
    :param body:
        邮件内容
    :param attach:
        邮件附件，可多项，用,分割。
    :param content_is_html:
        邮件内容是否是html格式的
    :return:
        执行成功返回True, 否则返回False, 并打印错误到stderr
    """
    cup.decorators.needlinux(mutt_sendmail)
    shell = cup.shell.ShellExec()
    temp_cwd = os.getcwd()

    str_att = ''
    cmdstr = ''
    if attach == '':
        if content_is_html is True:
            cmdstr = 'echo "%s"|/usr/bin/mutt -e "my_hdr Content-Type:'\
                'text/html" -s "%s" %s' \
                % (body, subject, tostr)
        else:
            cmdstr = 'echo "%s"|/usr/bin/mutt -s "%s" %s' % (
                body, subject, tostr
            )
    else:
        attlist = attach.strip().split(',')
        attlen = len(attlist)
        for i in range(0, attlen):
            str_att += '-a ' + attlist[i]
            if(i != attlen - 1):
                str_att += ' '
        if content_is_html is True:
            cmdstr = 'echo %s|/usr/bin/mutt -e "my_hdr Content-Type:'\
                'text/html" -s "%s" %s %s' % (body, subject, str_att, tostr)
        else:
            cmdstr = 'echo %s|/usr/bin/mutt -s "%s" %s %s' % (
                body, subject, str_att, tostr
            )
    ret_dic = shell.run(cmdstr, 60)
    os.chdir(temp_cwd)
    if ret_dic['returncode'] == 0:
        return True
    else:
        warnings.warn(ret_dic['stderr'])
        return False


class SmtpMailer(object):  # pylint: disable=R0903
    """
    :param sender: 设置发送人邮箱
    :param server: smtp的mailserver
    :param port: port
    :param is_html: body是否是html.

    如下有个支持html嵌入图片以及附件的例子
    我厂的smtp server hostname请自行babel搜索smtp服务器
    ::

        import cup
        mailer = cup.mail.SmtpMailer(
            'xxx@xxx.com',
            'xxxx.smtp.xxx.com',
            is_html=True
        )
        mailer.sendmail(
            [
                'maguannan@baidu.com',
                'liuxuan05@baidu.com',
                'zhaominghao@baidu.com'
            ],
            'test_img',
            (
                'testset <img src="cid:screenshot.png"></img>'
            ),
            [
                '/home/work/screenshot.png',
                '../abc.zip'
            ]
        )
    """
    _COMMA_SPLITTER = ','

    def __init__(
        self, sender, server, port=25, is_html=False
    ):
        """
        """
        self._server = None
        self._port = None
        self._sender = None
        self._is_html = False
        self.setup(sender, server, port, is_html)

    def setup(self, sender, server, port=25, is_html=False):
        """
        可在运行过程中更改发送设置
        """
        self._server = server
        self._port = port
        self._sender = sender
        self._is_html = is_html

    @classmethod
    def _check_type(cls, instance, type_list):
        if not type(instance) in type_list:
            raise TypeError(
                '%s only accepts types like: %s' %
                (instance, ','.join(type_list))
            )

    @classmethod
    def _handle_attachments(cls, outer, attachments):
        if type(attachments) == str:
            attrs = [attachments]
        elif type(attachments) == list:
            attrs = attachments
        else:
            attrs = []
        for attached in attrs:
            if not os.path.isfile(attached):
                log.warn('attached is not a file:%s' % attached)
                continue
            # Guess the content type based on the file's extension.  Encoding
            # will be ignored, although we should check for simple things like
            # gzip'd or compressed files.
            ctype, encoding = mimetypes.guess_type(attached)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed)
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            try:
                if maintype == 'text':
                    with open(attached) as fhandle:
                        # Note: we should handle calculating the charset
                        msg = text.MIMEText(fhandle.read(), _subtype=subtype)
                elif maintype == 'image':
                    with open(attached, 'rb') as fhandle:
                        imgid = os.path.basename(attached)
                        msg = image.MIMEImage(fhandle.read(), _subtype=subtype)
                        msg.add_header('Content-ID', imgid)
                elif maintype == 'audio':
                    with open(attached, 'rb') as fhandle:
                        msg = audio.MIMEAudio(fhandle.read(), _subtype=subtype)
                else:
                    with open(attached, 'rb') as fhandle:
                        msg = base.MIMEBase(maintype, subtype)
                        msg.set_payload(fhandle.read())
                    # Encode the payload using Base64
                    encoders.encode_base64(msg)
                    # Set the filename parameter
                    msg.add_header(
                        'Content-Disposition', 'attachment',
                        filename=os.path.basename(attached)
                    )
                outer.attach(msg)
            # pylint: disable=W0703
            except Exception as exception:
                log.warn(
                    'failed to attach %s, errmsg:%s. Will skip it' % (
                        attached, str(exception)
                    )
                )

    # pylint: disable=R0914,R0912,R0915
    def sendmail(self, recipients, subject='', body='', attachments=None,
        cc=None, bcc=None
    ):
        """
        发送邮件.

        :param recipients:
            支持传入一个邮件接收者(string), 或者邮件接受者list
        :param subject:
            邮件主题
        :param body:
            邮件正文
        :param attachments:
            支持传入一个附件(string类型,邮件路径)或者附件list路径列表.
            请注意, 需要传入绝对路径!
        :param cc:
            抄送列表. 可以传入一个string类型邮件抄送者. 也可以是一个
            list，里面每一个item是一个抄送者
        :param bcc:
            密送列表. 可以传入一个string类型邮件密送地址. 也可以是一个
            list，里面每一个item是一个密送地址
        :return:
            发送成功返回(True, None)的tuple, 失败返回(False, error_msg)的tuple

        """
        errmsg = None
        self._check_type(recipients, [str, list])
        self._check_type(subject, [str])
        toaddrs = []
        # self._check_type(body, [str])
        if self._is_html:
            msg_body = text.MIMEText(body, 'html', _charset='utf-8')
        else:
            msg_body = text.MIMEText(body, 'plain', _charset='utf-8')
        outer = multipart.MIMEMultipart()
        outer['Subject'] = subject
        if type(recipients) == list:
            outer['To'] = self._COMMA_SPLITTER.join(recipients)
            toaddrs.extend(recipients)
        else:
            outer['To'] = recipients
            toaddrs.append(recipients)
        if cc is not None:
            if type(cc) == str:
                outer['Cc'] = cc
                toaddrs.append(cc)
            elif type(cc) == list:
                outer['Cc'] = self._COMMA_SPLITTER.join(cc)
                toaddrs.extend(cc)
            else:
                raise TypeError('cc only accepts string or list')
        if bcc is not None:
            if type(bcc) == str:
                outer['Bcc'] = bcc
                toaddrs.append(bcc)
            elif type(bcc) == list:
                outer['Bcc'] = self._COMMA_SPLITTER.join(bcc)
                toaddrs.extend(bcc)
            else:
                raise TypeError('bcc only accepts string or list')
        outer['From'] = self._sender
        outer.preamble = 'Peace and Joy!\n'
        self._handle_attachments(outer, attachments)
        outer.attach(msg_body)
        # handle attachments
        composed = outer.as_string()
        try:
            smtp = smtplib.SMTP(self._server, self._port)
            smtp.sendmail(self._sender, toaddrs, composed)
            smtp.quit()
            return (True, None)
        except smtplib.SMTPException as smtperr:
            errmsg = str(smtperr)
            return (False, errmsg)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
