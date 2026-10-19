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

Synopsis: Read the repository sync settings and keep its job on the
django-q scheduler.
"""
import logging

from django_q.models import Schedule
from django_q.tasks import schedule

from base_app.models.app_configurations import AppConfiguration, CONFIGURATION_DEFINITIONS


SYNC_JOB_NAME = 'GRENML Repository Sync'
SYNC_TASK = 'repository_sync.tasks.sync_repository'

ENABLED_SETTING = 'GRENML_REPOSITORY_SYNC_ENABLED'
URL_SETTING = 'GRENML_REPOSITORY_SYNC_URL'
INTERVAL_SETTING = 'GRENML_REPOSITORY_SYNC_INTERVAL'

log = logging.getLogger(__name__)


def get_setting(name):
    """
    The configured value, or the setting's default when its row doesn't
    exist yet ("initialisesettings" runs after "migrate" on startup).
    """
    try:
        return AppConfiguration.objects.get(name=name).value
    except AppConfiguration.DoesNotExist:
        return CONFIGURATION_DEFINITIONS[name].default_value


def sync_enabled():
    return get_setting(ENABLED_SETTING) == 'True'


def schedule_sync(interval_minutes=None):
    """
    (Re)creates the scheduled sync job. The job always runs; the task
    itself checks the enabled setting, so toggling it needs no
    rescheduling.
    """
    if interval_minutes is None:
        interval_minutes = int(get_setting(INTERVAL_SETTING))
    Schedule.objects.filter(name=SYNC_JOB_NAME).delete()
    log.info(f'Scheduling the GRENML repository sync every {interval_minutes} minute(s)')
    schedule(
        SYNC_TASK,
        name=SYNC_JOB_NAME,
        schedule_type=Schedule.MINUTES,
        minutes=interval_minutes,
        repeats=-1,
    )
