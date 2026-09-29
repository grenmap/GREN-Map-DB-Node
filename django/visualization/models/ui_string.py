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

This file contains the models for fixed map interface vocabulary
(e.g. button/label text), translatable via LibreTranslate.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class UIString(models.Model):
    """
    A piece of fixed map interface vocabulary in its canonical
    English form, translatable via LibreTranslate.
    """
    key = models.SlugField(max_length=64, unique=True, verbose_name=_('key'))
    text = models.CharField(max_length=256, verbose_name=_('text'))

    class Meta:
        ordering = ('key',)
        verbose_name = _('UI String')
        verbose_name_plural = _('UI Strings')

    def __str__(self):
        return f'{self.key} = "{self.text}"'


class UIStringTranslation(models.Model):
    """
    Translated copy of a UIString, generated via LibreTranslate and
    cached here.
    """
    ui_string = models.ForeignKey(
        UIString,
        on_delete=models.CASCADE,
        related_name='translations',
        verbose_name=_('UI string'),
    )
    language_code = models.CharField(
        max_length=10, choices=settings.MAP_TRANSLATION_LANGUAGES,
        verbose_name=_('language code'),
    )
    text = models.CharField(max_length=256, blank=True, default='', verbose_name=_('text'))

    class Meta:
        unique_together = ('ui_string', 'language_code')
        verbose_name = _('UI String Translation')
        verbose_name_plural = _('UI String Translations')

    def __str__(self):
        return f'{self.ui_string.key} [{self.language_code}]'
