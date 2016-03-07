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
<<<<<<< HEAD
                'abc@baidu.com',
                'cde@baidu.com',
                'fff@baidu.com'
            ],
            'test_img',
            (
                'testset <img src="http://baidu.com/main/'
=======
                'maguannan@baidu.com',
                'file-qa@baidu.com'
            ],
            'test_img',
            (
                'testset <img src="http://abc/main/'
>>>>>>> origin/master
                'wp-content/uploads/2013/06/monkeyc.jpg"></img>'
            ),
            ['/home/work/test.txt']
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

    # pylint: disable=R0914,R0912,R0915
    def sendmail(self, recipients, subject='', body='', attachments=None):
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
        :return:
            发送成功返回(True, None)的tuple, 失败返回(False, error_msg)的tuple

        """
        errmsg = None
        self._check_type(recipients, [str, list])
        self._check_type(subject, [str])
        # self._check_type(body, [str])
        if self._is_html:
            msg_body = text.MIMEText(body, 'html', _charset='utf-8')
        else:
            msg_body = text.MIMEText(body, 'plain', _charset='utf-8')
        outer = multipart.MIMEMultipart()
        outer['Subject'] = subject
        if type(recipients) == list:
            outer['To'] = self._COMMA_SPLITTER.join(recipients)
        else:
            outer['To'] = recipients
        outer['From'] = self._sender
        outer.preamble = 'Peace and Joy!\n'
        outer.attach(msg_body)
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
                        msg = image.MIMEImage(fhandle.read(), _subtype=subtype)
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
        composed = outer.as_string()
        try:
            smtp = smtplib.SMTP(self._server, self._port)
            smtp.sendmail(self._sender, recipients, composed)
            smtp.quit()
            return (True, None)
        except smtplib.SMTPException as smtperr:
            errmsg = str(smtperr)
            return (False, errmsg)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
