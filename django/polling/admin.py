"""
Copyright 2023 GRENMap Authors

SPDX-License-Identifier: Apache License 2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
from requests import ConnectionError, get

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.urls import reverse, path
from django.conf import settings

# A string that should be translated and
# is in the module scope (outside a function or class)
# should be marked with gettext_lazy instead of gettext.
# Reference:
# https://docs.djangoproject.com/en/3.2/topics/i18n/translation/#lazy-translation
from django.utils.translation import gettext, gettext_lazy as _

from base_app.utils.access_control import is_in_production_mode
from .models import *


SINGLE_SOURCE_STATUS_SUCCESS_MESSAGE = _(
    # Translators: {} is the name of a machine on the network (polling peer)  # noqa
    '{} was successfully pinged'
)
SINGLE_SOURCE_STATUS_INVALID_CODE_MESSAGE = _(
    # Translators: first {} is the name of a machine on the network (polling peer), second is a number  # noqa
    'Was able to connect to {} but got status code {}.'
)
SINGLE_SOURCE_STATUS_CONNECTION_ERROR_MESSAGE = _(
    # Translators: {} is the name of a machine on the network (polling peer)  # noqa
    'Was unable to connect to {}.  Please review your configuration.'
)

MULTI_SOURCE_STATUS_SUCCESS_MESSAGE = _(
    # Translators: {}'s are numbers  # noqa
    'Contacted {} source(s). Got {} successful response(s).'
)
MULTI_SOURCE_STATUS_FAILURE_APPEND = _(
    # Translators: first {} is a number, second is a comma-separated list of names of machines in the network  # noqa
    ' Got {} error(s). Please check the configuration on source(s): {}'
)


log = logging.getLogger()


# Register polling source model
@admin.register(PollingSource)
class PollingSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'source_action_buttons')

    change_list_template = 'entities/polling_source_list.html'

    # Polling sources created in production will have default values for
    # protocol (HTTPS) and port (443).
    readonly_fields = ['protocol', 'port'] if is_in_production_mode() else []

    def get_urls(self):
        """
        Override the get_urls function to add the URLs needed for
        the admin button actions
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                '<source_id>/poll/',
                self.polling_action,
                name='source-polling'
            ),
            path(
                '<source_id>/status/',
                self.status_action,
                name='source-status'
            ),
            path(
                'poll-all/',
                self.polling_all_active_action,
                name='poll-all'
            ),
            path(
                'status-all/',
                self.status_all_action,
                name='status-all'
            ),
        ]
        return custom_urls + urls

    # Admin list related functions

    def source_action_buttons(self, obj):
        """
        Supply HTML to be inserted into the table for the action buttons
        """
        return format_html(
            '<a class="button" href="{}">{}</a>&nbsp'
            '<a class="button" href="{}">{}</a>',
            reverse('admin:source-polling', args=[obj.id]),
            gettext('Collect GRENML Data'),
            reverse('admin:source-status', args=[obj.id]),
            gettext('Test Connection'),
        )

    source_action_buttons.short_description = _('Polling Source Actions')
    source_action_buttons.allow_tags = True

    actions = ['check_status', 'poll_selected_sources']

    # Change the templates base on the view

    def add_view(self, request, form_url='', extra_context=None):
        self.change_form_template = super().change_form_template  # reset the template
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.change_form_template = 'entities/polling_source_change_form.html'
        return super().change_view(request, object_id, form_url, extra_context)

    # Admin form function overrides

    def response_change(self, request, obj):
        """
        Override the response_change to perform the actions of the
        status check if the status check button was clicked
        """
        if '_status_check' in request.POST:
            message, failure = self.check_single_status(obj)
            self.report_user(request, message, failure)
            return HttpResponseRedirect('.')
        return super().response_change(request, obj)

    # The Admin Drop-down Actions

    def check_status(self, request, queryset):
        message, failure = self.check_multiple_status(queryset)
        self.report_user(request, message, failure)

    def poll_selected_sources(self, request, queryset):
        """
        Admin action to poll all sources selected in list view.
        Initiates an asynchronous (Django-Q) cycle managed by a
        PollImport object.
        """
        log.info('Initiating batch poll triggered via Admin.')

        batch_poll_import = BatchPollImport.objects.create(polling_sources=list(queryset))
        batch_poll_import.execute()

        message = _('Batch poll initiated; imports in progress.')
        self.report_user(request, message, False)

    check_status.short_description = gettext('Check the Status of Selected Sources')
    poll_selected_sources.short_description = gettext('Poll the Selected Sources')

    # Status check related actions

    def status_action(self, request, source_id):
        source = PollingSource.objects.get(id=source_id)
        message, failure = self.check_single_status(source)
        self.report_user(request, message, failure)
        return HttpResponseRedirect('../../')

    def status_all_action(self, request):
        queryset = PollingSource.objects.all()
        message, failure = self.check_multiple_status(queryset)
        self.report_user(request, message, failure)
        return HttpResponseRedirect('../')

    # Polling related actions

    def polling_action(self, request, source_id):
        """
        Admin button action to poll a single source from a button.
        Initiates an asynchronous (Django-Q) cycle managed by a
        PollImport object.
        """
        log.info('Initiating single-source poll triggered via Admin.')

        polling_source = PollingSource.objects.get(pk=source_id)
        batch_poll_import = BatchPollImport.objects.create(polling_sources=[polling_source])
        batch_poll_import.execute()

        message = _('Poll and import initiated.')
        self.report_user(request, message, False)
        return HttpResponseRedirect('../../')

    def polling_all_active_action(self, request):
        """
        Admin button action to poll a all sources marked as 'active'.
        Initiates an asynchronous (Django-Q) cycle managed by a
        PollImport object.
        """
        log.info('Initiating batch poll of all active sources triggered via Admin.')

        batch_poll_import = BatchPollImport.objects.create()
        batch_poll_import.execute()

        message = _('Full batch poll and import for all active sources initiated.')
        self.report_user(request, message, False)
        return HttpResponseRedirect('../')

    # Utility functions

    def report_user(self, request, message, failure):
        if failure:
            self.message_user(request, message, level=messages.ERROR)
        else:
            self.message_user(request, message)

    @staticmethod
    def check_single_status(obj):
        failure = False
        try:
            r = get(
                obj.status_url,
                verify=is_in_production_mode(),
                timeout=settings.REQUEST_TIMEOUT)
            if r.ok:
                message = SINGLE_SOURCE_STATUS_SUCCESS_MESSAGE.format(obj.name)
            else:
                failure = True
                message = SINGLE_SOURCE_STATUS_INVALID_CODE_MESSAGE.format(
                    obj.name, r.status_code
                )
        except ConnectionError:
            log.exception('PollingSourceAdmin.check_single_status')
            failure = True
            message = SINGLE_SOURCE_STATUS_CONNECTION_ERROR_MESSAGE.format(obj.name)

        return message, failure

    def check_multiple_status(self, queryset):
        success = 0
        failures = []
        failure_count = 0
        for source in queryset.all():
            i, fail = self.check_single_status(source)
            if not fail:
                success += 1
            else:
                failure_count += 1
                failures.append(source.name)
        message = MULTI_SOURCE_STATUS_SUCCESS_MESSAGE.format(queryset.count(), success)
        if failures:
            message += MULTI_SOURCE_STATUS_FAILURE_APPEND.format(
                failure_count, ', '.join(failures)
            )
        return message, bool(failure_count)


class PollImportAdminInline(admin.TabularInline):
    """
    Django Admin view for subordinate PollImport objects
    for view on a BatchPollImport page.
    """
    model = PollImport
    fk_name = 'batch_poll_import'
    min_num = 0
    extra = 0

    fields = (
        'polling_source',
        'status',
        'status_message',
        'poll_start',
        'poll_duration_seconds',
        'import_start',
        'import_duration_seconds',
        'grenml_data',
    )

    readonly_fields = [
        'poll_start',
        'import_start',
        'grenml_data',
    ]

    def has_add_permission(self, request, obj=None):
        """
        Disallow manual creation of new objects.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Render entire object read-only.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Disallow deletion of objects.
        """
        return False

    @admin.display(description=_('poll start'))
    def poll_start(self, obj):
        return obj.poll_datetime.strftime('%H:%M:%S')

    @admin.display(description=_('import start'))
    def import_start(self, obj):
        return obj.import_datetime.strftime('%H:%M:%S')

    @admin.display(description=_('GRENML data'))
    def grenml_data(self, obj):
        if obj.grenml_data_import:
            return format_html(
                '<a href="{}">{}</a>',
                reverse(
                    'admin:grenml_import_importdata_change',
                    args=[obj.grenml_data_import.pk],
                ),
                str(obj.grenml_data_import),
            )
        else:
            return '-'


@admin.register(BatchPollImport)
class BatchPollImportAdmin(admin.ModelAdmin):
    """
    Django Admin view for BatchPollImport.
    Individual view will include all subordinate PollImport objects.
    """
    inlines = [PollImportAdminInline]

    list_display = (
        'timestamp',
        'was_scheduled',
        'num_sources',
        'poll_import_status',
        'running_duration',
    )

    fields = (
        'was_scheduled',
        'duration_seconds',
        'status_synopsis',
    )

    readonly_fields = [
        'status_synopsis',
    ]

    def has_add_permission(self, request, obj=None):
        """
        Disallow manual creation of new objects.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Render entire object read-only.
        """
        return False

    @admin.display(description=_('number of sources'))
    def num_sources(self, obj):
        return len(obj.polls.all())

    @admin.display(description=_('poll import status'))
    def poll_import_status(self, obj):
        status = obj.overall_status
        if status == PollImport.STATUS_ABORTED:
            return '❗️'
        elif status == PollImport.STATUS_COMPLETE:
            return '✅'
        else:
            return '🕑'

    @admin.display(description=_('running duration (seconds)'))
    def running_duration(self, obj):
        if obj.status:
            return obj.duration_seconds
        else:
            return obj._time_taken(save=False)

    @admin.display(description=_('status synopsis'))
    def status_synopsis(self, obj):
        """
        Returns a human-language summary of the status of a batch
        poll-and-import job.
        e.g.
            Batch status: Running
            6 sources total
            ✅ Complete: 4
            🚧 In progress: 2
        e.g.
            Batch status: Complete
            10 sources total
            ✅ Complete: 10
        e.g.
            Batch status: Complete
            2 sources total
            ✅ Complete: 1
            ❗️ Aborted due to error: 1
        e.g.
            Batch status: Running
            1 source total
            🕑 Pending: 1
        """
        num_sources = self.num_sources(obj)
        status_list = obj.status_list
        num_complete = status_list.count(PollImport.STATUS_COMPLETE)
        num_pending = status_list.count(PollImport.STATUS_PENDING)
        num_aborted = status_list.count(PollImport.STATUS_ABORTED)
        num_in_progress = num_sources - num_complete - num_pending - num_aborted

        if obj.status:
            message = gettext('Batch status: Complete')
        else:
            message = gettext('Batch status: Running')
        message += '\n'

        if num_sources == 1:
            message += gettext(
                # Translators: {} is a placeholder for a number  # noqa
                '{} source total'
            ).format(num_sources)
        else:
            message += gettext(
                # Translators: {} is a placeholder for a number  # noqa
                '{} sources total'
            ).format(num_sources)
        message += '\n'

        if num_complete:
            message += gettext(
                # Translators: {} is a placeholder for a number. The icon is part of the message.  # noqa
                '✅ Complete: {}'
            ).format(num_complete)
            message += '\n'

        if num_in_progress:
            message += gettext(
                # Translators: {} is a placeholder for a number. The icon is part of the message.  # noqa
                '🚧 In progress: {}'
            ).format(num_in_progress)
            message += '\n'

        if num_pending:
            message += gettext(
                # Translators: {} is a placeholder for a number. The icon is part of the message.  # noqa
                '🕑 Pending: {}'
            ).format(num_pending)
            message += '\n'

        if num_aborted:
            message += gettext(
                # Translators: {} is a placeholder for a number. The icon is part of the message.  # noqa
                '❗️ Aborted due to error: {}'
            ).format(num_aborted)
            message += '\n'

        return message
