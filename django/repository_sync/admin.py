"""
Copyright 2026 GRENMap Authors

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
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from repository_sync.models import RepositorySyncState


@admin.register(RepositorySyncState)
class RepositorySyncStateAdmin(admin.ModelAdmin):
    """
    Read-only view of what the repository sync last did, with an
    action to run it right away. Configuration lives in the App
    Configuration Settings (GRENML_REPOSITORY_SYNC_*).
    """
    list_display = (
        '__str__', 'last_status', 'last_checked_at', 'last_imported_at', 'last_sha256',
    )
    readonly_fields = (
        'source_url', 'last_status', 'last_checked_at', 'last_imported_at',
        'last_sha256', 'last_import', 'last_message',
    )
    fields = readonly_fields
    actions = ['sync_now']

    @admin.action(description=_('Sync now (even if sync is disabled)'))
    def sync_now(self, request, queryset):
        async_task('repository_sync.tasks.sync_repository', force=True)
        self.message_user(
            request,
            _('Sync started; reload this page in a moment to see the result.'),
            messages.SUCCESS,
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
