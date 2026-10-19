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
from django.db import models
from django.utils.translation import gettext_lazy as _

from grenml_import.models import ImportData


class RepositorySyncState(models.Model):
    """
    Single row recording what the repository sync last saw and did,
    so it only imports when the GRENML file actually changes.
    """
    SINGLETON_PK = 1

    STATUS_NEVER_RUN = 'never_run'
    STATUS_UNCHANGED = 'unchanged'
    STATUS_IMPORTED = 'imported'
    STATUS_DOWNLOAD_FAILED = 'download_failed'
    STATUS_IMPORT_FAILED = 'import_failed'
    STATUS_CHOICES = [
        (STATUS_NEVER_RUN, _('Never run')),
        (STATUS_UNCHANGED, _('Unchanged')),
        (STATUS_IMPORTED, _('Imported')),
        (STATUS_DOWNLOAD_FAILED, _('Download failed')),
        (STATUS_IMPORT_FAILED, _('Import failed')),
    ]

    source_url = models.CharField(
        max_length=500, blank=True, default='',
        verbose_name=_('source URL'),
    )
    last_sha256 = models.CharField(
        max_length=64, blank=True, default='',
        verbose_name=_('SHA-256 of the last imported file'),
    )
    last_checked_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('last checked at'),
    )
    last_imported_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('last imported at'),
    )
    last_status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default=STATUS_NEVER_RUN,
        verbose_name=_('last status'),
    )
    last_message = models.TextField(blank=True, default='', verbose_name=_('last message'))
    last_import = models.ForeignKey(
        ImportData,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('last import'),
    )

    @classmethod
    def get(cls):
        state, _created = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return state

    def __str__(self):
        return str(_('GRENML repository sync'))

    class Meta:
        verbose_name = _('GRENML Repository Sync')
        verbose_name_plural = _('GRENML Repository Sync')
