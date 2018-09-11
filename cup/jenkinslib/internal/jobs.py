#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Jobs object.
Jobs is a container of Job.
"""

from cup.jenkinslib.internal import exception


class Jobs(object):
    """A container of Job objects."""
    def __init__(self, jenkins):
        """initialize Jobs object."""
        self.jenkins = jenkins
        jenkins.poll()

    def __setitem__(self, job_name, config):
        """create new job."""
        return self.create(job_name, config)

    def __getitem__(self, job_name):
        """get job by name."""
        for row in self.jenkins._data.get('jobs', []):
            if row['name'] == job_name:
                return self.jenkins.Job(row['url'], row['name'], self.jenkins)
        raise exception.UnknownJob(job_name)

    def __delitem__(self, job_name):
        """delete job by name."""
        retry = 3
        while job_name in self and retry:
            try:
                delete_job_url = self[job_name].get_delete_url()
                self.jenkins.requester.post_and_confirm_status(
                    delete_job_url,
                    data='some random bytes...')
                self.jenkins.poll()
            except exception.JenkinsAPIError:
                retry -= 1

    def __contains__(self, job_name):
        """job exists or not."""
        return job_name in self.keys()

    def __len__(self):
        """job num."""
        return len(self.keys())

    def __iter__(self):
        """iterator for job names."""
        return (row['name'] for row in self.jenkins._data.get('jobs', []))

    def iterkeys(self):
        """get all job name."""
        for row in self.jenkins._data.get('jobs', []):
            yield row['name']

    def keys(self):
        """get all job name."""
        return list(self.iterkeys())

    def create(self, job_name, config):
        """create new job.

        Args:
            job_name: name of new job.
            config: configure for new job, xml text.

        Returns:
            new job object.
        """
        if job_name in self:
            return self[job_name]

        params = {'name': job_name}
        self.jenkins.requester.post_xml_and_confirm_status(
            self.jenkins.get_create_url(),
            data=config,
            params=params)

        self.jenkins.poll()
        if job_name not in self:
            raise exception.JenkinsAPIError('Cannot create job %s' % job_name)

        return self[job_name]

    def rename(self, job_name, new_job_name):
        """rename a job.

        Args:
            job_name: name of a existing job.
            new_job_name: new job name.

        Returns:
            new job object.
        """
        params = {'newName': new_job_name}
        rename_job_url = self[job_name].get_rename_url()
        self.jenkins.requester.post_and_confirm_status(
            rename_job_url,
            data="",
            params=params)
        self.jenkins.poll()
        return self[new_job_name]

