"""
.. moduleauthor:: Sandeep Nanda <sandeep.nanda@guavus.com>

Models used by Potluck Web UI
"""

from django.db import models
from django.conf import settings
from django.utils.timezone import now

import subprocess
import time
import logging
import re

logger = logging.getLogger(__name__)

class Solution(models.Model):
    name = models.CharField(max_length=512)

    def __unicode__(self):
        return self.name

class Build(models.Model):
    solution = models.ForeignKey("Solution")
    version = models.CharField(max_length=512)
    platform_version = models.CharField(max_length=512)
    image_path = models.CharField(max_length=2048, help_text="Full Image URL e.g. http://192.168.0.17/release/appanalytics/2.0/2.0.d1/appanalytics2.0.d1/image-appanalytics2.0.d1.img")

    def __unicode__(self):
        return "%s %s" % (self.solution, self.version)

    @property
    def total_count(self):
        if not hasattr(self, "_total_count"):
            self._total_count = self.testsuiteexecution_set.filter(state=TestsuiteExecution.COMPLETED).count()
        return self._total_count

    @property
    def pass_percent(self):
        if self.total_count == 0:
            return 0
        return (self.pass_count * 100) / self.total_count

    @property
    def fail_percent(self):
        if self.total_count == 0:
            return 0
        return (self.fail_count * 100) / self.total_count

    @property
    def pass_count(self):
        if not hasattr(self, "_pass_count"):
            self._pass_count = self.testsuiteexecution_set.filter(status=TestsuiteExecution.Status.PASSED).count()
        return self._pass_count

    @property
    def fail_count(self):
        if not hasattr(self, "_fail_count"):
            self._fail_count = self.testsuiteexecution_set.filter(status=TestsuiteExecution.Status.FAILED).count()
        return self._fail_count

class TestsuiteExecution(models.Model):
    # Constants
    ENQUEUED, RUNNING, COMPLETED, LIMBO = 1, 2, 3, 4
    STATE_CHOICES = (
        (ENQUEUED, "Enqueued"),
        (RUNNING, "Running"),
        (COMPLETED, "Completed"),
        (LIMBO, "LIMBO"),
    )
    class Status:
        PASSED, FAILED = 1, 2
    STATUS_CHOICES = (
        (Status.PASSED, "Passed"),
        (Status.FAILED, "Failed"),
    )

    # Fields
    build = models.ForeignKey("Build")
    suite = models.CharField(max_length=512)
    testbed = models.CharField(max_length=512)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    ui_url = models.CharField(max_length=512, blank=True, null=True, verbose_name="Url of the UI")
    started_at = models.DateTimeField(null=True, blank=True, default=now)
    completed_at = models.DateTimeField(null=True, blank=True)
    state = models.IntegerField(choices=STATE_CHOICES, default=ENQUEUED)
    status = models.IntegerField(choices=STATUS_CHOICES, null=True, blank=True)
    logs_path = models.TextField()
    harness_output = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "%s's execution on testbed '%s' <%s>" % (self.build, self.testbed, self.pk)

    @property
    def has_started(self):
        return self.started_at is not None

    @property
    def has_completed(self):
        return self.completed_at is not None

    @property
    def is_running(self):
        return self.state == TestsuiteExecution.RUNNING

    @property
    def total_count(self):
        if not hasattr(self, "_total_count"):
            self._total_count = self.testcaseexecution_set.count()
        return self._total_count

    @property
    def pass_count(self):
        if not hasattr(self, "_pass_count"):
            self._pass_count = self.testcaseexecution_set.filter(status=TestcaseExecution.Status.PASSED).count()
        return self._pass_count

    @property
    def fail_count(self):
        if not hasattr(self, "_fail_count"):
            self._fail_count = self.testcaseexecution_set.filter(status=TestcaseExecution.Status.FAILED).count()
        return self._fail_count

    @property
    def executed_count(self):
        if not hasattr(self, "_executed_count"):
            self._executed_count = self.testcaseexecution_set.exclude(status=TestcaseExecution.Status.SKIPPED).count()
        return self._executed_count

    @property
    def pass_percent(self):
        if self.total_count == 0:
            return 0
        return (self.pass_count * 100) / self.total_count

    @models.permalink
    def get_absolute_url(self):
        return ("show_testrun", (self.pk,))

    @models.permalink
    def get_logs_url(self):
        return ("show_logs", (self.logs_path,))

    @models.permalink
    def get_reschedule_url(self):
        return ("reschedule_testrun", (self.pk,))

    def get_report_url(self):
        logs_url = self.get_logs_url()
        if logs_url:
            return logs_url + "/report.html"
        else:
            return ""

    def do_start(self, started_at=None, save=True):
        if started_at is not None:
            self.started_at = started_at
        else:
            self.started_at = now()

        self.state = TestsuiteExecution.RUNNING
        self.testcaseexecution_set.all().delete()
        if save is True:
            self.save()

    def do_complete(self, completed_at=None, save=True):
        if completed_at is None:
            self.completed_at = now()
        else:
            self.completed_at = completed_at
        self.state = TestsuiteExecution.COMPLETED
        # Make sure all the test cases are marked as completed
        self.testcaseexecution_set.filter(completed_at=None).update(completed_at=self.completed_at)
        if self.pass_percent < 100:
            self.status = TestsuiteExecution.Status.FAILED
        else:
            self.status = TestsuiteExecution.Status.PASSED
        if save is True:
            self.save()

    def run(self):
        """Runs the actual harness command"""
        harness_cmd = "%s/harness --dbid %s" % (settings.POTLUCK.ROOT_DIR, self.pk)
        try:
            logger.info("Running %s..." % self.pk)
            p = subprocess.Popen(harness_cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = p.communicate()
            logger.debug(stdout)
            self.harness_output = stdout.strip()
        finally:
            if not self.has_completed:
                self.do_complete()

    def reschedule(self, user):
        return TestsuiteExecution.objects.create(build=self.build, suite=self.suite, testbed=self.testbed, ui_url=self.ui_url, user=user)

class TestcaseExecution(models.Model):
    # Constants
    class Status:
        PASSED, FAILED, SKIPPED = 1, 2, 3

    STATUS_CHOICES = (
        (Status.PASSED, "Passed"),
        (Status.FAILED, "Failed"),
        (Status.SKIPPED, "Skipped"),
    )
    class State:
        NOT_RUN, RUNNING, COMPLETED, LIMBO = 1, 2, 3, 4

    STATE_CHOICES = (
        (State.NOT_RUN, "Not Run"),
        (State.RUNNING, "Running"),
        (State.COMPLETED, "Completed"),
        (State.LIMBO, "LIMBO"),
    )

    # Fields
    suite_execution = models.ForeignKey(TestsuiteExecution)
    tc_id = models.CharField(max_length=256)
    script = models.CharField(max_length=512)
    section = models.CharField(max_length=512)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    logs_path = models.TextField()
    state = models.IntegerField(choices=STATE_CHOICES, default=State.NOT_RUN)
    status = models.IntegerField(choices=STATUS_CHOICES, default=Status.SKIPPED)
    remarks = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return "Testcase <%s>" % self.script

    def complete(self, save=True):
        self.completed_at = now()
        if save is True:
            self.save()

    @property
    def has_started(self):
        return self.started_at is not None

    @property
    def has_completed(self):
        return self.completed_at is not None

    @property
    def is_running(self):
        return self.has_started and not self.has_completed

    def do_start(self, save=True):
        self.state = TestcaseExecution.State.RUNNING
        if save is True:
            self.save()

    def do_complete(self, completed_at=None, save=True):
        if completed_at is None:
            self.completed_at = now()
        else:
            self.completed_at = completed_at
        self.state = TestcaseExecution.State.COMPLETED
        if save is True:
            self.save()

    def get_logs_url(self):
        if not self.logs_path:
            return ""
        else:
            if self.logs_path.startswith("/"):
                return "/logs%s" % self.logs_path
            else:
                return "/logs/%s" % self.logs_path

    def reschedule(self, user):
        """Reschedule only this one testcase"""
        return TestsuiteExecution.objects.create(build=self.suite_execution.build,
                                                suite=None,
                                                testbed=self.suite_execution.testbed,
                                                ui_url=self.suite_execution.ui_url,
                                                user=user)
