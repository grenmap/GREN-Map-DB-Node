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

------------------------------------------------------------------------
Synopsis: This file contains the API that return the xml file with the
grenmap db node
"""

import json
import logging

from django.http import HttpResponse
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.decorators import api_view

from base_app.constants import COLLECT_TOKEN_MESSAGE, SNAPSHOT_FILE_MESSAGE
from base_app.models import AppConfiguration
from base_app.serializers import (
    AccessDeniedSerializer,
    ErrorSerializer,
    GRENMLExportSerializer,
)
from base_app.utils.decorators import check_token, always_check_token
from grenml_export.exporter import GRENMLExporter
from published_network_data.views.api import create_published_network_data_response

logger = logging.getLogger()


def _download_grenml(request):
    """
    Handles polling requests. The response sent by this function
    will have all the network data in the node.
    """
    try:
        exporter = GRENMLExporter()
        stream = exporter.to_stream()
        response = HttpResponse(stream.getvalue(), content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="grenml.xml"'
        return response
    except Exception as e:
        exception_name = e.__class__.__name__
        logger.exception('_download_grenml (%s)', exception_name)
        return HttpResponse(
            json.dumps({'error_type': exception_name}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type='application/json',
        )


@extend_schema(
    description=_(
        # Translators: <br> is an HTML tag that inserts a new line.  # noqa
        'Depending on the server\'s "Polling Data Supply Type" '
        'configuration parameter, <br> '
        'returns the root topology in the database '
        'as a GRENML file, or the latest snapshot file created. <br> <br> '
        'All nodes, links and institutions under the root topology '
        'and its child topologies <br> '
        'are saved in the file when the server creates it. <br> <br> '
        'To see or modify the supply type parameter, '
        'go to the admin site and <br> '
        'navigate to Home > Base App > App Configuration Settings. <br> <br> '
    ) + SNAPSHOT_FILE_MESSAGE + COLLECT_TOKEN_MESSAGE,
    auth=[{'polling token': []}],
    tags=[],
    responses={
        ('200', '*/*'): GRENMLExportSerializer,
        ('403', 'application/json'): AccessDeniedSerializer,
        ('500', 'application/json'): ErrorSerializer,
    }
)
@api_view(['GET'])
@check_token
def download_grenml_by_type(request):
    """
    Decorated handler that checks the access token
    if the node is not in development mode.
    """
    try:
        setting_data_type = AppConfiguration.objects.get(
            name='GRENML_POLLING_DATA_SUPPLY_TYPE',
        ).value
    except AppConfiguration.DoesNotExist:
        setting_data_type = 'Live'

    if setting_data_type == 'Live':
        return _download_grenml(request)
    elif setting_data_type == 'Published':
        return create_published_network_data_response(request)


@api_view(['GET', 'POST'])
@always_check_token
def test_download_grenml(request):
    """ Test endpoint handler. This always checks the access token. """
    return _download_grenml(request)
