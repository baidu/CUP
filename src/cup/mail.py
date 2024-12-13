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
import time
import warnings
import mimetypes
import smtplib
import contextlib
from email.mime import multipart
from email import encoders
from email.mime import audio
from email.mime import base
from email.mime import image
from email.mime import text

from cup import log
from cup import shell
from cup import thread
from cup import platforms
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
        # if your smtp server needs login , pls uncomment line below:
        # mailer.login(usernname, password)
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
    RETRY_LOGIN_TIMES = 3

    def __init__(self, sender, server, port=25, ssl=False):
        """

        :param sender:
            sender email address,  xxx@xxx.com
        :param server:
            smtp server
        :param port:
            25 by default
        :param is_html:
            is email format a html style, False by default.
            You can set it to True if the email format is html based.

        """
        self._server = server
        self._port = port
        self._sender = sender
        self._login_params = ('', '')
        self.setup(sender, server, port)
        self._ssl = ssl
        self._lock = thread.RWLock()
        with self.lockit():
            if ssl:
                self._smtpser = smtplib.SMTP_SSL(self._server, self._port)
            else:
                self._smtpser = smtplib.SMTP(self._server, self._port)

    def setup(self, sender: str, server: str, port=25):
        """
        change parameters during run-time
        """
        self._server = server
        self._port = port
        self._sender = sender

    def login(self, username: str, passwords: str) -> bool:
        """
        if the smtp need login, plz call this method before you call
        sendmail
        """
        log.info('smtp server will login with user {0}'.format(username))
        self._login_params = (username, passwords)
        new_login_params = (username, passwords)
        if new_login_params != self._login_params:
            log.info(
                f"smtp sender username/passwords changed, "
                "from {self._login_params[0]}/* to {username}/*"
            )
            self._login_params:tuple[str, str] = (username, passwords)
        retry_times = SmtpMailer.RETRY_LOGIN_TIMES
        while retry_times > 0:
            try:
                self._smtpser.login(
                    self._login_params[0], self._login_params[1]
                )
                status = self._smtpser.noop()
                if status[0] == 250:
                    return True
            except smtplib.SMTPException as err:
                log.error(f'failed to login into smtpserver {err}')
            time.sleep(0.5)
            retry_times -= 1
        log.error('failed to login into smtpserver')
        return False

    @classmethod
    def _check_type(cls, instance, type_list):
        if not type(instance) in type_list:
            raise TypeError(
                '%s only accepts types like: %s' %
                (instance, ','.join(type_list))
            )
        
    def get_attachment_content(self, attached):
        """
            get attachment_content
            
            :param attached:
                local path of a file

        """
        content = None
        with open(attached, 'rb') as fhandle:
            content = fhandle.read()
        return content
    
    def check_file_valid(self, attached):
        """check if the file is valid"""
        if not os.path.isfile(attached):
            log.warn('attached is not a file:%s' % attached)
            return False
        return True

    def _handle_attachments(self, outer, attachments):
        if type(attachments) == str:
            attrs = [attachments]
        elif type(attachments) == list:
            attrs = attachments
        else:
            attrs = []
        for attached in attrs:
            if not self.check_file_valid(attached):
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
                content = self.get_attachment_content(attached)
                if maintype == 'text':
                    # with open(attached, 'rb') as fhandle:
                        # Note: we should handle calculating the charset
                    msg = text.MIMEText(
                        content.decode(), _subtype=subtype
                    )
                elif maintype == 'image':
                    imgid = os.path.basename(attached)
                    msg = image.MIMEImage(
                        content, _subtype=subtype
                    )
                    msg.add_header('Content-ID', imgid)
                elif maintype == 'audio':
                    msg = audio.MIMEAudio(
                        content, _subtype=subtype)
                else:
                    msg = base.MIMEBase(maintype, subtype)
                    msg.set_payload(content)
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
    
    @contextlib.contextmanager
    def lockit(self):
        """
        lock it
        """
        self._lock.acquire_writelock()
        try:
            yield
        except:
            pass
        finally:
            self._lock.release_writelock()
            

    # pylint: disable=R0914,R0912,R0915
    def sendmail(self, recipients, subject='', body='', attachments=None,
        cc=None, bcc=None, ishtml=False
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
        toaddrs: list[str] = []
        # self._check_type(body, [str])
        if ishtml:
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
            if platforms.is_str_py2py3(cc):
                outer['Cc'] = cc
                toaddrs.append(cc)
            elif isinstance(cc, list):
                outer['Cc'] = self._COMMA_SPLITTER.join(cc)
                toaddrs.extend(cc)
            else:
                raise TypeError('cc only accepts string or list')
        if bcc is not None:
            if platforms.is_str_py2py3(cc):
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
        ret: tuple = (False, 'failed to send email')
        retry = SmtpMailer.RETRY_LOGIN_TIMES
        login_try = True
        while retry > 0:
            retry -= 1
            try:
                status = self._smtpser.noop() 
                if status[0] != 250:
                    continue
                self._smtpser.sendmail(self._sender, toaddrs, composed)
                ret = (True, None)
                break
            except (
                smtplib.SMTPSenderRefused, smtplib.SMTPConnectError, 
                smtplib.SMTPServerDisconnected, smtplib.SMTPAuthenticationError
            ) as err:
                log.info('failed to send mail {0}, will retry'.format(err))
                if login_try:
                    log.debug('login smtp server to send email')
                    with self.lockit():
                        if self._ssl:
                            self._smtpser = smtplib.SMTP_SSL(
                                self._server, self._port
                            )
                        else:
                            self._smtpser = smtplib.SMTP(
                                self._server, self._port
                            )
                        self._smtpser.ehlo_or_helo_if_needed()
                        if self.login(
                            self._login_params[0], self._login_params[1]
                        ):
                            retry += 1
                            login_try = False
            except smtplib.SMTPException as smtperr:
                ret = (False, '{0}'.format(smtperr))
                log.error('failed to send mail {0}'.format(smtperr))

        return ret


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
