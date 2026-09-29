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
------------------------------------------------------------------------

This file contains the model caching LibreTranslate translations of
an Institution's popup_summary/popup_content, for the GRENMap
visualization popup.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from network_topology.models import Institution


class InstitutionPopupTranslation(models.Model):
    """
    Translated copies of an Institution's popup_summary/popup_content,
    generated via LibreTranslate and cached here.
    """
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name='visualization_popup_translations',
        verbose_name=_('institution'),
    )
    language_code = models.CharField(
        max_length=10, choices=settings.LANGUAGES,
        verbose_name=_('language code'),
    )
    summary = models.TextField(blank=True, default='', verbose_name=_('summary'))
    full_content = models.TextField(blank=True, default='', verbose_name=_('full content'))

    class Meta:
        unique_together = ('institution', 'language_code')
        verbose_name = _('Institution Popup Translation')
        verbose_name_plural = _('Institution Popup Translations')

    def __str__(self):
        return f'{self.institution.name} popup [{self.language_code}]'
