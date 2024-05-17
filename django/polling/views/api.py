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

Synopsis: Polling API
"""

import logging

from django.utils.translation import gettext as _
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from base_app.utils.decorators import test_only
from base_app.models.app_configurations import AppConfiguration
from polling.app_configurations import PollingEnabledSetting, PollingIntervalSetting
from polling.models.sources import PollingSource
from polling.models.control import BatchPollImport
from polling.serializers.sources import PollingSourceSerializer
from polling.serializers.control import BatchPollImportSerializer, BatchPollImportDetailSerializer


log = logging.getLogger(__name__)


# *** Polling Triggers ***


@api_view(['POST'])
def trigger_batch_poll(request):
    """
    Triggers the polling task to gather and process all active GRENML
    sources, only if the GRENML_POLLING_ENABLED setting allows it.

    Returns the relative URL of the poll event log in the HTTP Location
    header, with 201 CREATED code.  If the setting disallows a poll,
    returns 403 FORBIDDEN.  Returns the expected 500 ERROR if a problem
    with polling or ingestion is encountered.  Returns 204 NO CONTENT
    if there are no active polling sources to poll.
    """
    # Ensure that polling has not been disabled
    if AppConfiguration.objects.get(name='GRENML_POLLING_ENABLED').value == 'False':
        log.warning('Batch poll via API has been interrupted: polling is currently disabled.')
        return Response(
            _('Polling is currently disabled'),
            status=status.HTTP_403_FORBIDDEN,
        )

    log.info('Initiating full batch poll triggered via API.')

    # The query string should indicate whether this is a scheduled run
    # or an impromptu manually-triggered poll
    scheduled = bool(int(request.GET.get('scheduled', '0')))

    if not PollingSource.objects.filter(active=True).exists():
        log.info('No active polling sources.  Cancelling batch poll.')
        return Response(
            data=_('No active polling sources.'),
            status=status.HTTP_204_NO_CONTENT,
        )

    batch_poll_import = BatchPollImport.objects.create(was_scheduled=scheduled)
    batch_poll_import.execute()

    # Use the returned log object to assess the success of the polling
    # run and formulate a return value accordingly
    response = Response('', status=status.HTTP_201_CREATED)
    response['Location'] = reverse('polling-log-batch-detail', args=[batch_poll_import.id])
    return response


@test_only
@api_view(['POST'])
def trigger_source_poll(request, id):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Triggers a polling task for an individual polling source.
    Returns the relative URL of the batch poll event log in the
    HTTP Location header.
    """
    try:
        polling_source = PollingSource.objects.get(pk=id)
    except PollingSource.DoesNotExist:
        return Response(
            f'PollingSource with ID {id} does not exist.',
            status=status.HTTP_404_NOT_FOUND,
        )
    log.info(f'Initiating single source poll of {polling_source} triggered via API.')

    batch_poll_import = BatchPollImport.objects.create(polling_sources=[polling_source])
    batch_poll_import.execute()

    response = Response('', status=status.HTTP_201_CREATED)
    response['Location'] = reverse('polling-log-batch-detail', args=[batch_poll_import.id])
    return response


# *** Polling Source REST ***


@test_only
@api_view(['GET', 'POST'])
def sources(request):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Basic CRUD for polling sources:
        - see a list of items (GET)
        - add a new item (POST)

    Example POST JSON input:
    {
        "name": "test",
        "protocol": "http",
        "hostname": "localhost",
        "port": "8080",
        "path": "",
        "active": true
    }
    """
    if request.method == 'GET':
        polling_sources = PollingSource.objects.all()
        serializer = PollingSourceSerializer(polling_sources, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PollingSourceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            response['Location'] = reverse('polling-source-detail', args=[serializer.data['id']])
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@test_only
@api_view(['GET', 'PATCH', 'DELETE'])
def source_detail(request, id):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Basic CRUD for an individual polling source:
        - see an item (GET)
        - edit fields of an item (PATCH)
        - remove an item (DELETE)

    Example PATCH JSON input:
    {
        "name": "test",
        "protocol": "http",
        "hostname": "localhost",
        "port": "8080",
        "path": "",
        "active": true
    }
    or any subset of those fields.
    Note that editing the ID field is not supported.
    """
    if request.method == 'GET':
        try:
            polling_source = PollingSource.objects.get(id=id)
            serializer = PollingSourceSerializer(polling_source)
            return Response(serializer.data)
        except PollingSource.DoesNotExist:
            return Response(
                'Polling source not found.',
                status=status.HTTP_404_NOT_FOUND,
            )

    elif request.method == 'PATCH':
        try:
            polling_source = PollingSource.objects.get(id=id)
            serializer = PollingSourceSerializer(polling_source, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PollingSource.DoesNotExist:
            return Response(
                'Polling source not found.',
                status=status.HTTP_404_NOT_FOUND,
            )

    elif request.method == 'DELETE':
        try:
            polling_source = PollingSource.objects.get(id=id)
            polling_source.delete()
        except PollingSource.DoesNotExist:
            # If it doesn't exist, fail silently for idempotency
            pass
        return Response('', status=status.HTTP_204_NO_CONTENT)


# *** Poll Event Log REST ***


@test_only
@api_view(['GET'])
def batch_poll_event_logs(request):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Basic CRUD for batch polling event logs:
        - see a list of items (GET)
    """
    serializer = BatchPollImportSerializer(BatchPollImport.objects.all(), many=True)
    return Response(serializer.data)


@test_only
@api_view(['GET'])
def batch_poll_event_log_detail(request, id):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Basic CRUD for an individual batch polling event log:
        - see an item (GET)
    """
    try:
        batch_poll_import = BatchPollImport.objects.get(pk=id)
        serializer = BatchPollImportDetailSerializer(batch_poll_import)
        return Response(serializer.data)
    except BatchPollImport.DoesNotExist:
        return Response(
            'Batch poll import event log not found.',
            status=status.HTTP_404_NOT_FOUND,
        )


# *** Configuration API ***


@test_only
@api_view(['GET'])
def automatic_polling_enabled(request):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Reports the current enabled state of automatic polling:
    "True" or "False"
    """
    setting = AppConfiguration.objects.get(name=PollingEnabledSetting.name)
    return Response(setting.value)


@test_only
@api_view(['PUT'])
def automatic_polling_toggle(request, enable=0):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Sets the enabled state by specifying either 0 (False) or a positive
    integer (True) as part of the URL.

    Reports the resultant enabled state of automatic polling:
    "True" or "False"
    """
    enabled_setting_value = str(bool(enable))
    setting = AppConfiguration.objects.get(name=PollingEnabledSetting.name)
    setting.value = enabled_setting_value
    setting.save()
    return Response(setting.value)


@test_only
@api_view(['GET', 'PUT'])
def automatic_polling_interval(request):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.
    Sets and retrieves the automatic polling interval setting string.

    PUT input should be JSON of the form:
    {
        "interval": "<desired interval setting string>"
    }
    The string must represent valid crontab format, and is so validated.
    If empty JSON is provided, resets to the default value.

    PUT & GET both report the current setting value.
    """
    setting = AppConfiguration.objects.get(name=PollingIntervalSetting.name)
    if request.method == 'PUT':
        new_interval_setting_value = request.data.get(
            'interval',
            PollingIntervalSetting.default_value,
        )
        setting.value = new_interval_setting_value
        try:
            setting.clean()
            setting.save()
        except ValidationError as e:
            return Response(e.error_list, status=status.HTTP_400_BAD_REQUEST)
    return Response(setting.value)
