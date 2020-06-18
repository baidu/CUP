#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    mail related modules.

    **Recommand using SmtpMailer**
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
from cup import shell
from cup import decorators


def mutt_sendmail(  # pylint: disable=R0913,W0613
    tostr, subject, body, attach, content_is_html=False
):
    """
    Plz notice this function is not recommanded to use. Use SmtpMailer instead.

    :param  exec_cwd:
        exec working directory. Plz use
    :param tostr:
        recipt list, separated by ,
    :param subject:
        subject
    :param body:
        email content
    :param attach:
        email attachment
    :param content_is_html:
        is htm mode opened
    :return:
        return True on success, False otherwise
    """
    decorators.needlinux(mutt_sendmail)
    shellobj = shell.ShellExec()
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
    ret_dic = shellobj.run(cmdstr, 60)
    os.chdir(temp_cwd)
    if ret_dic['returncode'] == 0:
        return True
    else:
        warnings.warn(ret_dic['stderr'])
        return False


class SmtpMailer(object):  # pylint: disable=R0903
    """
    :param sender:  mail sender
    :param server: smtp的mailserver
    :param port: port
    :param is_html:  is html enabled

    smtp server examples
    ::

        from cup import mail
        mailer = mail.SmtpMailer(
            'xxx@xxx.com',
            'xxxx.smtp.xxx.com',
            is_html=True
        )
        mailer.sendmail(
            [
                'maguannan',
                'liuxuan05',
                'zhaominghao'
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
        self, sender, server='mail2-in.baidu.com', port=25, is_html=False
    ):
        """
        """
        self._server = None
        self._port = None
        self._sender = None
        self._is_html = False
        self._login_params = None
        self.setup(sender, server, port, is_html)

    def setup(self, sender, server, port=25, is_html=False):
        """
        change parameters during run-time
        """
        self._server = server
        self._port = port
        self._sender = sender
        self._is_html = is_html

    def login(self, username, passwords):
        """
        if the smtp need login, plz call this method before you call
        sendmail
        """
        log.info('smtp server will login with user {0}'.format(username))
        self._login_params = (username, passwords)

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
                    with open(attached, 'rb') as fhandle:
                        # Note: we should handle calculating the charset
                        msg = text.MIMEText(
                            fhandle.read(), _subtype=subtype
                        )
                elif maintype == 'image':
                    with open(attached, 'rb') as fhandle:
                        imgid = os.path.basename(attached)
                        msg = image.MIMEImage(
                            fhandle.read(), _subtype=subtype
                        )
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
        send mail

        :param recipients:
            "list" of recipients. See the example above
        :param subject:
            subject
        :param body:
            body of the mail
        :param attachments:
            "list" of attachments. Plz use absolute file path!
        :param cc:
            cc list
        :param bcc:
            bcc list
        :return:
            return (True, None) on success, return (False, error_msg) otherwise
        """
        errmsg = None
        # self._check_type(recipients, [str, list])
        # self._check_type(subject, [str])
        toaddrs = []
        # self._check_type(body, [str])
        if self._is_html:
            msg_body = text.MIMEText(body, 'html', _charset='utf-8')
        else:
            msg_body = text.MIMEText(body, 'plain', _charset='utf-8')
        outer = multipart.MIMEMultipart()
        outer['Subject'] = subject
        if isinstance(recipients, list):
            outer['To'] = self._COMMA_SPLITTER.join(recipients)
            toaddrs.extend(recipients)
        else:
            outer['To'] = recipients
            toaddrs.append(recipients)
        if cc is not None:
            if type(cc) == str:
                outer['Cc'] = cc
                toaddrs.append(cc)
            elif isinstance(cc, list):
                outer['Cc'] = self._COMMA_SPLITTER.join(cc)
                toaddrs.extend(cc)
            else:
                raise TypeError('cc only accepts string or list')
        if bcc is not None:
            if type(bcc) == str:
                outer['Bcc'] = bcc
                toaddrs.append(bcc)
            elif isinstance(bcc, list):
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
        ret = (False, 'failed to send email')
        try:
            smtp = smtplib.SMTP(self._server, self._port)
            if self._login_params is not None:
                smtp.login(self._login_params[0], self._login_params[1])
            smtp.sendmail(self._sender, toaddrs, composed)
            smtp.quit()
            ret = (True, None)
        except smtplib.SMTPException as smtperr:
            ret = (False, str(errmsg))
        return ret


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
