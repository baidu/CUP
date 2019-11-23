#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian,
"""
This module provides Queue object.
"""

import time
from cup.jenkinslib.internal import base
from cup.jenkinslib.internal import exception


class Queue(base.JenkinsBase):
    """Represents a jenkins queue."""
    def __init__(self, url, jenkins):
        """initialize Queue object."""
        self.jenkins = jenkins
        super(Queue, self).__init__(url, static=jenkins.is_static)

    def __str__(self):
        return self.url

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.jenkins

    def iteritems(self):
        """iterator of items."""
        for item in self._data['items']:
            queue_id = item['id']
            item_url = "%s/item/%i" % (self.url, queue_id)
            yield item['id'], QueueItem(url=item_url, jenkins=self.jenkins)

    def iterkeys(self):
        """iterator of keys."""
        for item in self._data['items']:
            yield item['id']

    def itervalues(self):
        """iterator of values."""
        for item in self._data['items']:
            yield QueueItem(self.jenkins, **item)

    def keys(self):
        """keys of items in queue."""
        return list(self.iterkeys())

    def values(self):
        """values of items in queue."""
        return list(self.itervalues())

    def __len__(self):
        return len(self._data['items'])

    def __getitem__(self, item_id):
        self_as_dict = dict(self.iteritems())
        if item_id in self_as_dict:
            return self_as_dict[item_id]
        else:
            raise exception.UnknownQueueItem(item_id)

    def _get_queue_items_for_job(self, job_name):
        for item in self._data["items"]:
            if item['task']['name'] == job_name:
                yield QueueItem(self.get_queue_item_url(item), 
                                jenkins=self.jenkins)

    def get_queue_items_for_job(self, job_name):
        """get queue items by job name."""
        return list(self._get_queue_items_for_job(job_name))

    def get_queue_item_url(self, item):
        """get url of queue item."""
        return "%s/item/%i" % (self.url, item["id"])

    def delete_item(self, queue_item):
        """delete item in queue."""
        self.delete_item_by_id(queue_item.queue_id)

    def delete_item_by_id(self, item_id):
        """delete item by id."""
        deleteurl = '%s/cancelItem?id=%s' % (self.url, item_id)
        self.get_jenkins_obj().requester.post_url(deleteurl)


class QueueItem(base.JenkinsBase):
    """Represents an item in jenkins queue."""
    def __init__(self, url, jenkins):
        """initialize QueueItem object."""
        self.jenkins = jenkins
        super(QueueItem, self).__init__(url, static=jenkins.is_static)

    @property
    def queue_id(self):
        """get id of queue item."""
        return self._data['id']

    @property
    def name(self):
        """get task name of queue item."""
        return self._data['task']['name']

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.jenkins

    @property
    def job(self):
        """get Job object associated with queue item."""
        return self.jenkins.get_job(self.name)

    @property
    def parameters(self):
        """get parameters of queue item."""
        actions = self._data.get('actions', [])
        for action in actions:
            if type(action) is dict and 'parameters' in action:
                parameters = action['parameters']
                return dict([(x['name'], x.get('value', None))
                             for x in parameters])
        return []

    def __str__(self):
        return "%s Queue #%i" % (self.name, self.queue_id)

    @property
    def build(self):
        """get build object of this queue item."""
        job_name = self.job_name
        build_number = self.build_number
        return self.jenkins[job_name][build_number]

    def block_until_complete(self, delay=15, timeout=None):
        """block until task of this queue item build and complete."""
        if self.is_static:
            raise exception.ImappropriateMethodInStaticMode("block_until_complete")

        stime = time.time()
        build = self.block_until_building(delay)
        if timeout is not None:
            waited = time.time() - stime
            if timeout < waited:
                raise exception.RunTimeout("wait %is > %is, timeout!" % (waited, timeout))

            timeout -= waited
        return build.block_until_complete(delay=delay, timeout=timeout)

    def block_until_building(self, delay=15, timeout=None):
        """block until task of this queue item build."""
        if self.is_static:
            raise exception.ImappropriateMethodInStaticMode("block_until_building")

        stime = time.time()
        while True:
            try:
                self.poll()
                return self.build
            except exception.NotBuiltYet:
                pass

            waited = time.time() - stime
            if timeout is not None and timeout < waited:
                raise exception.RunTimeout("wait %is > %is, timeout!" % (waited, timeout))

            time.sleep(delay)

    @property
    def is_running(self):
        """check queue item is running or not."""
        try:
            build = self.build
            if build:
                return build.is_running
        except exception.NotBuiltYet:
            return False
        return False

    @property
    def build_number(self):
        """get build number if exists."""
        try:
            return self._data['executable']['number']
        except KeyError:
            raise exception.NotBuiltYet()

    @property
    def job_name(self):
        """get job name if exists."""
        try:
            return self._data['task']['name']
        except KeyError:
            raise exception.NotBuiltYet()
