"""
Copyright 2020 GRENMap Authors

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
from django.db import models
from grenml_export.exporter import GRENMLExporter
from django_q.tasks import async_task
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger()


def version():
    return datetime.utcnow().strftime('%Y-%m-%dT%H%M%S')


class PublishedNetworkData(models.Model):

    version = models.CharField(max_length=128, verbose_name=_('version'))
    file_contents = models.TextField(null=True, verbose_name=_('file contents'))
    name = models.CharField(max_length=128, verbose_name=_('name'))
    file_date = models.DateTimeField(auto_now_add=True, verbose_name=_('file date'))
    published_status = models.CharField(
        default='pending',
        max_length=128,
        verbose_name=_('published status'),
    )
    grenml_export_description = models.TextField(
        default='',
        verbose_name=_('GRENML export description'),
    )

    @property
    def published_state(self):
        return self.published_status
    published_state.fget.short_description = _('published state')

    def save(self, *args, **kwargs):
        if not self.version:
            self.version = version()
        super(PublishedNetworkData, self).save(*args, **kwargs)

    def __str__(self):
        return self.grenml_export_description

    class Meta:
        verbose_name = _('Published Database Snapshot')
        verbose_name_plural = _('Published Database Snapshots')


def published(instance):
    try:
        exporter = GRENMLExporter()
        output_stream = exporter.to_stream()
        PublishedNetworkData.objects.filter(id=instance.id).update(
            file_contents=output_stream.getvalue(),
            published_status="success"
        )
    except Exception:
        logger.exception('Exporting to grenml failed with exception')
        PublishedNetworkData.objects.filter(id=instance.id).update(
            file_contents=None,
            published_status="Exporting Failed with exception"
        )


@receiver(post_save, sender=PublishedNetworkData)
def post_save(instance, **kwargs):
    logger.info('In PublishedNetworkData post_save, run grenml_export')
    async_task(published, instance)
