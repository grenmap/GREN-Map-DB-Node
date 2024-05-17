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

------------------------------------------------------------------------

Synopsis: Helpers to set the polling interval on the cron scheduler.
"""
import logging
import os
import requests

from django_q.tasks import schedule
from django_q.models import Schedule
from django.conf import settings


# Polling url on app container
POLLING_URL = os.environ.get('POLLING_URL', 'http://app:8080/polling/trigger/?scheduled=1')

# Name of the scheduled job
POLLING_JOB_NAME = 'GRENML Source Polling'


log = logging.getLogger(__name__)


def execute_polling_job(url, expected_code):
    """
    Executes the polling job by POSTing to the polling url
    """
    log.info(f'execute_polling_job by posting to: {url}')
    try:
        request_response = requests.post(
            url,
            timeout=settings.REQUEST_TIMEOUT)
        if request_response.status_code == expected_code:
            log.info('Successfully started polling request')
        else:
            log.error(
                'Could not trigger polling request. '
                f'Status: {request_response.status_code}'
            )
    except requests.exceptions.Timeout:
        log.error('Timeout executing polling request')
    except requests.exceptions.RequestException:
        log.error(f'Connection to polling url refused: {url}')
    except Exception:
        log.exception('execute_polling_job failed')
    log.debug('execute_polling_job completed posting')


def schedule_job(polling_interval, polling_url=POLLING_URL):
    """
    Schedules a polling job with the given interval on the scheduler
    """
    # First remove an existing schedule
    if Schedule.objects.filter(name=POLLING_JOB_NAME).exists():
        log.debug('Delete existing schedule')
        Schedule.objects.filter(name=POLLING_JOB_NAME).delete()

    log.info(
        f'Schedule a polling job with the given interval: {polling_interval} on the scheduler')
    schedule('polling.utils.schedule_polling.execute_polling_job',
             name=POLLING_JOB_NAME,
             schedule_type=Schedule.CRON,
             cron=polling_interval,
             **{
                 'expected_code': 201,
                 'url': polling_url
             }
             )
