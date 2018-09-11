#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Artifacts and FTPArtifacts object.
"""

import ftplib
import os
import pprint
import socket
import urlparse

from cup.jenkinslib.internal import exception


class ArtifactsBase(object):
    """Base of artifacts."""
    def __init__(self, build, name="", path="", is_dir=True):
        """initialize Artifacts object."""
        self.children = None
        self.build = build
        self.name = name
        self.path = path
        self.is_dir = is_dir

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.build.job.jenkins

    def poll(self):
        """poll out artifacts info."""
        if self.children is None and self.is_dir:
            self.children = self._poll()
        return self.children

    def _poll(self):
        """poll out artifacts info."""
        raise exception.NotImplementedMethod("_poll")

    def download(self, path="./"):
        """download these artifacts.

        Args:
            path: local path to store artifacts, if not exists, create it.
        """
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError as err:
                if not os.path.isdir(path):
                    raise exception.OSIOError(err)

        self._download(path)

    def _download(self, path="./"):
        """do download."""
        raise exception.NotImplementedMethod("_download")

    def get_child_artifacts(self, child):
        """get child artifacts by filename or dirname."""
        if not self.is_dir:
            raise exception.NoArtifacts(child)

        self.poll()
        try:
            return self.children[child]
        except KeyError:
            items = child.split('/', 1)
            if len(items) > 1 and items[0] in self.children:
                return self.children[items[0]][items[1]]
            raise exception.NoArtifacts(child)

    def __getitem__(self, child):
        """get child artifacts by filename or dirname."""
        return self.get_child_artifacts(child)

    def pprint(self):
        """print all the child of this object."""
        return pprint.pprint(self.children)

    def __str__(self):
        return self.path

    @property
    def url(self):
        """get artifact url."""
        raise exception.NotImplementedMethod("url")


class Artifacts(ArtifactsBase):
    """Represents artifacts, file or directory."""
    pass


class FTPArtifacts(ArtifactsBase):
    """Represents artifacts on FTP.

    Because ftp connection is used, close should be called if connected.
    It is recommended to use with as like:
            with FTPArtifacts(build) as af:
                bin_af = af["bin"]
                bin_af.download("./output")
    """
    def __init__(self, build, name="", path="", is_dir=True):
        """initialize FTPArtifacts object."""
        self.ftp = None
        super(FTPArtifacts, self).__init__(build, name, path, is_dir)

    def connect(self):
        """connect to ftp, return ftp connection."""
        if self.ftp is None:
            jenkins = self.get_jenkins_obj()
            if jenkins.ftp_host is None:
                raise exception.FtpError("cannot connect to ftp server before enable ftp")

            self.ftp = ftplib.FTP()
            try:
                self.ftp.connect(jenkins.ftp_host, jenkins.ftp_port)
                self.ftp.login(jenkins.ftp_username, jenkins.ftp_password)
            except ftplib.error_perm as err:
                self.ftp.close()
                self.ftp = None
                raise exception.FtpError(err)
            except socket.error as err:
                self.ftp.close()
                self.ftp = None
                raise exception.FtpError(err)

        return self.ftp

    def __enter__(self):
        """connect to ftp, return self."""
        self.connect()
        return self

    def close(self):
        """close ftp connection."""
        if self.ftp:
            self.ftp.close()
            self.ftp = None

    def __exit__(self, type, value, traceback):
        """close ftp connection."""
        self.close()
        return False

    def _poll(self, tree=None):
        """poll out artifacts info."""
        def do_poll(ftp_conn):
            """do poll with connected ftp connection."""
            child_list = []
            ftp_conn.dir(self.path, child_list.append)

            children = {}
            for child in child_list:
                name = child.split()[-1]
                sub_path = os.path.join(self.path, name)
                is_dir = child.startswith("d")
                children[name] = self.__class__(self.build, name, sub_path, is_dir)

            return children

        if self.ftp:
            return do_poll(self.ftp)

        with self:
            return do_poll(self.ftp)

    def _download(self, path="./", ftp=None):
        """do download."""
        def do_download(ftp_conn):
            """do download with connected ftp connection."""
            save_path = os.path.join(path, self.name)

            if self.is_dir:
                if not os.path.isdir(save_path):
                    os.makedirs(save_path)

                children = self.poll()
                for child in children:
                    with children[child] as af:
                        # download child with same ftp connection
                        af._download(save_path, ftp)
            else:
                try:
                    with open(save_path, "w+") as fd:
                        ftp_conn.retrbinary(u"RETR %s" % self.path, fd.write)
                except OSError as err:
                    raise exception.FtpError(err)
                except IOError as err:
                    raise exception.FtpError(err)

        if ftp:
            do_download(ftp)
        elif self.ftp:
            do_download(self.ftp)
        else:
            with self:
                do_download(self.ftp)

    @property
    def url(self):
        """get ftp artifact url."""
        jenkins = self.get_jenkins_obj()
        if jenkins.ftp_host is None:
            raise exception.FtpError("cannot get ftp url before enable ftp")

        netloc = []
        if jenkins.ftp_username:
            netloc.append(jenkins.ftp_username)
            if jenkins.ftp_password:
                netloc.append(":")
                netloc.append(jenkins.ftp_password)
            netloc.append("@")

        netloc.append(jenkins.ftp_host)
        if jenkins.ftp_port:
            netloc.append(":")
            netloc.append(str(jenkins.ftp_port))

        netloc = "".join(netloc)
        return urlparse.urlunparse(("ftp", netloc, self.path, "", "", ""))

