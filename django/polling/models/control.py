"""
SPDX-License-Identifier: Apache License 2.0

Copyright 2023 GRENMap Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

------------------------------------------------------------------------

Synopsis: Django models for co-ordinating the polling and importing of
    data from polling sources subordinate in the distributed hierarchy.
"""

import logging
from typing import List, Optional
from datetime import timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django_q.tasks import async_task

from network_topology.models import Topology
from network_topology.exceptions import MoreThanOneMainTopologyError
from grenml_import.models import ImportData, ImportAborted
from polling.models.sources import PollingSource
from polling.exceptions import SourcePollError


# Purges cached GRENML data stored in PollImport after successful
# imports to reduce database size creep
PURGE_GRENML_DATA_AFTER_IMPORT = True


log = logging.getLogger()


class BatchPollImportManager(models.Manager):
    """
    Custom Django ORM Manager for BatchPollImport that overrides
    the create method for convenience.
    """
    def create(self, *args, polling_sources: Optional[List[PollingSource]] = None, **kwargs):
        """
        Custom create method for a manager to support convenient
        creation of individual PollImport objects for the batch.
        If polling_sources is omitted, it will poll all active sources.

        Usage example:
            polling_sources = PollingSource.objects.filter(active=True)
            batch_poll_import = BatchPollImport.objects.create(
                was_scheduled=False,
                polling_sources=list(polling_sources),
            )
        """
        if not polling_sources:
            polling_sources = list(PollingSource.objects.filter(active=True))

        obj = super().create(*args, **kwargs)

        for polling_source in polling_sources:
            PollImport.objects.create(
                batch_poll_import=obj,
                polling_source=polling_source,
            )

        return obj


class BatchPollImport(models.Model):
    """
    Co-ordinator object to manage polling a list of PollingSources
    for GRENML data, then importing it.  Delegates each individual
    poll-import to a PollImport object.  Executes poll-imports in a
    serial fashion, each in its own asynchronous task.

    Public method execute() is an alias for _dispatch_source().
    Each call to _dispatch_source() creates an asynchronous
    task (using Django-Q) for a poll-import from a single source.
    Upon completion of that poll-import, it will create another
    async task for the next source in the remaining list,
    until the list has been exhausted.

    Tracks elapsed time from instantiation to last task completion.

    Usage example:
        polling_sources = PollingSource.objects.filter(active=True)
        batch_poll_import = BatchPollImport.objects.create(
            was_scheduled=False,
            polling_sources=list(polling_sources),
        )
        batch_poll_import.execute()
    """
    # Whether the polling event was scheduled or triggered manually
    was_scheduled = models.BooleanField(
        default=False,
        # Translators: (polling) was scheduled
        verbose_name=_('was scheduled'),
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('timestamp'),
    )

    duration_seconds = models.FloatField(
        default=0.0,
        verbose_name=_('duration seconds'),
    )

    # Status becomes True after all individual PollImports are complete
    status = models.BooleanField(
        default=False,
        verbose_name=_('status'),
    )

    objects = BatchPollImportManager()

    def _time_taken(self, save=True):
        """
        Simple helper to calculate the time elapsed between 'now' and
        when the batch was initiated (in self.timestamp), then update
        the duration_seconds field if the 'save' parameter is set,
        which is the default.  Be careful to run this judiciously, as
        it may overwrite existing stored values.
        """
        now = timezone.now()
        difference = now - self.timestamp
        difference_in_seconds = difference.total_seconds()
        if save:
            self.duration_seconds = difference_in_seconds
            self.save()
        return difference_in_seconds

    def _dispatch_source(self):
        """
        Given a list of PollImport objects related to this model,
        picks one from the list that has a status indicating it's
        ready (PollImport.STATUS_PENDING) and creates an asynchronous
        Django-Q task that runs _execute_source_poll_import() with that
        PollImport as its argument.
        Expects _execute_source_poll_import to call _dispatch_source()
        again when it has completed its task, creating a loop.
        This loop will be broken when there are no more ready
        PollImports in the list.
        """
        # Check to make sure this instance still exists in the DB.
        # Allows deletion of the object to kill the loop if necessary.
        try:
            BatchPollImport.objects.get(pk=self.pk)
        except BatchPollImport.DoesNotExist:
            return

        poll_imports_ready = self.polls.filter(status=PollImport.STATUS_PENDING)
        if poll_imports_ready.count():
            poll_import = poll_imports_ready.first()
            async_task(
                BatchPollImport._execute_source_poll_import,
                self,
                poll_import,
            )
        else:
            self._finish()

    def _execute_source_poll_import(self, poll_import):
        """
        Asynchronous task callback target for _dispatch_source().
        Accepts a single PollImport as argument.  Runs two methods:
        poll() and grenml_import() in sequence.  Once those have
        been completed, calls _dispatch_source() again to resume
        the serial-asynchronous loop.
        """
        # Poll for data
        poll_import.poll()
        # Import the data polled in the previous step
        # But if the poll for data has failed, skip the import
        # and proceed to the next source.
        if poll_import.status == PollImport.STATUS_POLLED:
            poll_import.grenml_import()

        # Trigger an asynchronous task for the next import in the chain
        self._dispatch_source()

    def execute(self):
        """
        Initiates a serial-asynchronous loop to poll and import all
        polling sources specified when creating this BatchPollImport.
        """
        log.info(f'Poll+import batch {self.pk} {self.timestamp} initiated.')
        self._dispatch_source()

    def _finish(self):
        """
        Updates elapsed time and status fields after all polling and
        importing has been completed.
        """
        self._time_taken()
        self.status = True
        self.save()
        log.info(
            f'Poll+import batch {self.pk} {self.timestamp} complete.  '
            f'Took {self.duration_seconds} seconds.  '
            f'Status: {self.overall_status}'
        )

    @property
    def status_list(self):
        """
        Returns a list of status values from each PollImport related
        to this BatchPollImport, in no particular order.
        Useful for a more detailed progress update than the overall
        boolean 'status' field directly on this object.
        """
        return list(self.polls.values_list('status', flat=True))

    @property
    def overall_status(self):
        """
        Inspects all of the PollImport objects related to this
        BatchPollImport to ascertain a more detailed overall status
        for the batch run.
        Returns for the following cases:
            - All tasks completed: PollImport.STATUS_COMPLETE
            - Any aborted task: PollImport.STATUS_ABORTED
            - Other mixed statuses: PollImport.STATUS_PENDING
        """
        status_list = self.status_list
        if not status_list:
            return PollImport.STATUS_COMPLETE

        if PollImport.STATUS_ABORTED in status_list:
            return PollImport.STATUS_ABORTED
        if list(set(status_list)) == [PollImport.STATUS_COMPLETE]:
            return PollImport.STATUS_COMPLETE
        else:
            return PollImport.STATUS_PENDING

    def __str__(self):
        return _(
            # Translators: {} is a placeholder for a date-time  # noqa
            'Poll and import batch at {}'
        ).format(str(self.timestamp))

    class Meta:
        verbose_name = _('Poll+Import Event')
        verbose_name_plural = _('Poll+Import Events')


class PollImport(models.Model):
    """
    Executes and tracks a poll for data from a PollingSource and the
    import of that data into the database (via importing's
    GRENMLImporter class).  Generally associated with a BatchPollImport
    that will dispatch those tasks asynchronously as it sees fit.
    """
    STATUS_ABORTED = -1
    STATUS_PENDING = 0
    STATUS_POLLING = 1
    STATUS_POLLED = 2
    STATUS_IMPORTING = 3
    STATUS_COMPLETE = 4
    STATUS_CHOICES = [
        (STATUS_ABORTED, _('Aborted')),
        (STATUS_PENDING, _('Pending')),
        (STATUS_POLLING, _('Polling')),
        (STATUS_POLLED, _('Polled; awaiting import')),
        (STATUS_IMPORTING, _('Importing')),
        (STATUS_COMPLETE, _('Complete')),
    ]

    batch_poll_import = models.ForeignKey(
        BatchPollImport,
        null=False, blank=False,
        on_delete=models.CASCADE,
        related_name='polls',
        verbose_name=_('batch poll import'),
    )

    polling_source = models.ForeignKey(
        PollingSource,
        null=False, blank=False,
        on_delete=models.CASCADE,
        related_name='polls',
        verbose_name=_('polling source'),
    )

    status = models.SmallIntegerField(
        null=False, blank=False,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_('status'),
    )
    status_message = models.CharField(
        max_length=255,
        null=True, blank=True,
        verbose_name=_('status message'),
    )

    grenml_data_import = models.OneToOneField(
        ImportData,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='poll_import',
        verbose_name=_('GRENML data import'),
    )

    # Timestamp to indicate the time the polling event started
    poll_datetime = models.DateTimeField(null=True, blank=True)
    # The length of time taken from when the polling event was triggered
    # until it completed.
    poll_duration_seconds = models.FloatField(
        default=0.0,
        verbose_name=_('poll duration seconds'),
    )

    # Timestamp to indicate the time the import event started
    import_datetime = models.DateTimeField(null=True, blank=True)
    # The length of time taken from when the import event was triggered
    # until it completed.
    import_duration_seconds = models.FloatField(
        default=0.0,
        verbose_name=_('import duration seconds'),
    )

    def _time_taken(self, start_datetime):
        """
        Helper function to abstract the datetime arithmetic used by
        more specific elapsed-time methods in this class.
        """
        now = timezone.now()
        difference = now - start_datetime
        difference_in_seconds = difference.total_seconds()
        return difference_in_seconds

    def _poll_time_taken(self, save=True):
        """
        Simple helper to calculate the time elapsed between 'now' and
        when the poll was initiated (in self.poll_datetime), then update
        the poll_duration_seconds field if the 'save' parameter is set,
        which is the default.  Be careful to run this judiciously, as
        it may overwrite existing stored values.
        """
        difference_in_seconds = self._time_taken(self.poll_datetime)
        if save:
            self.poll_duration_seconds = difference_in_seconds
            self.save()
        return difference_in_seconds

    def _import_time_taken(self, save=True):
        """
        Simple helper to calculate the time elapsed between 'now' and
        when the import of polled data was initiated (in
        self.import_datetime), then update the import_duration_seconds
        field if the 'save' parameter is set, which is the default.
        Be careful to run this judiciously, as it may overwrite
        existing stored values.
        """
        difference_in_seconds = self._time_taken(self.import_datetime)
        if save:
            self.import_duration_seconds = difference_in_seconds
            self.save()
        return difference_in_seconds

    @property
    def total_time(self):
        """
        Returns total elapsed seconds between the beginning of a poll
        operation to the end of the import operation, making the
        assumption that they occur in that order (should be enforced)
        and have both occurred (else return None).
        """
        if self.poll_datetime and self.import_datetime:
            end_datetime = self.import_datetime + timedelta(seconds=self.import_duration_seconds)
            time_delta = end_datetime - self.poll_datetime
            return time_delta.total_seconds()
        else:
            return None
    total_time.fget.short_description = _('total time seconds')

    @property
    def running_time(self):
        """
        Returns a tally of the total elapsed time (in seconds) consumed
        by the poll and import processes.
        """
        return self.poll_duration_seconds + self.import_duration_seconds
    running_time.fget.short_description = _('running time seconds')

    def poll(self):
        """
        Executes the poll() method on the related PollingSource
        object to gather GRENML data, and stores it in the model
        linked in the 'grenml_data_import' field.  Tracks start
        time (poll_timestamp) and elapsed time (poll_duration_seconds).
        """
        log.info(f'Polling source: {self.polling_source}')
        self.status = self.STATUS_POLLING
        self.poll_datetime = timezone.now()
        self.save()
        try:
            self.grenml_data_import = ImportData.objects.create(
                source=str(self.polling_source) + ' ' + _('poll'),
                grenml_data=self.polling_source.poll(),
            )
            self.status = self.STATUS_POLLED
        except (SourcePollError, Exception) as e:
            log.exception(f'Polling error for: {self.polling_source}')
            self.status = self.STATUS_ABORTED
            self.status_message = _('Polling error: ') + str(e)
        self.save()
        self._poll_time_taken()

    def grenml_import(self):
        """
        Using the GRENML data stored in the model linked in the
        'grenml_data_import' field, imports it into the database using
        that model's appropriate method.
        Tracks start time (import_timestamp) and elapsed time
        (import_duration_seconds).  If appropriately configured via the
        PURGE_GRENML_DATA_AFTER_IMPORT constant, discards the GRENML
        data after successful import, to slow database size creep.
        """
        if self.status < self.STATUS_POLLED:
            log.warning(f'PollImport {self} status indicates not ready for importing.')
            return

        log.info(f'Importing data from {self.polling_source}')
        self.status = self.STATUS_IMPORTING
        self.import_datetime = timezone.now()
        self.save()

        # Locate main root Topology as parent, if possible
        try:
            main_topology = Topology.objects.get_main_topology()
        except MoreThanOneMainTopologyError:
            main_topology = None

        try:
            self.grenml_data_import.execute_import(parent_topology=main_topology)
            self.status = self.STATUS_COMPLETE
            if PURGE_GRENML_DATA_AFTER_IMPORT:
                self.grenml_data_import.grenml_data = ''
                self.grenml_data_import.save()
        except ImportAborted as e:
            self.status = self.STATUS_ABORTED
            self.status_message = _('Import aborted: ') + str(e)
        self.save()
        self._import_time_taken()

    def __str__(self):
        return _(
            # Translators: first {} is the name of a machine on the network, second is a date-time  # noqa
            'Poll and import from {} at {}'
        ).format(str(self.polling_source), str(self.poll_datetime))
