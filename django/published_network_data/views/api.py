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

import logging

from django.http import HttpResponse
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view

from base_app.constants import COLLECT_TOKEN_MESSAGE, SNAPSHOT_FILE_MESSAGE
from base_app.serializers import AccessDeniedSerializer, GRENMLExportSerializer
from base_app.utils.decorators import check_token, always_check_token
from published_network_data.utils.published_data import get_published_data

log = logging.getLogger(__name__)


def create_published_network_data_response(request):
    """
    Responds to requests for the published data
    (snapshots of the network database).
    """
    try:
        stream = get_published_data()
        response = HttpResponse(stream.getvalue(), content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="published_data.xml"'
        return response
    except:  # noqa: E722
        log.exception('published_network_data failed')
        return HttpResponse(
            'Failed to find the published data file', status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    description=_(
        # Translators: <br> is an HTML tag that inserts a new line. Please keep both at the end of the message.  # noqa
        "Returns the snapshot of the server's data, as a GRENML file. <br> <br> "
    ) + SNAPSHOT_FILE_MESSAGE + COLLECT_TOKEN_MESSAGE,
    auth=[{'polling token': []}],
    tags=[],
    responses={
        ('200', '*/*'): GRENMLExportSerializer,
        ('403', 'application/json'): AccessDeniedSerializer,
    }
)
@api_view(['GET'])
@check_token
def published_network_data(request):
    """
    Handles requests for the network data snapshot.
    Checks the access token if not in development mode.
    """
    return create_published_network_data_response(request)


@api_view(['POST'])
@always_check_token
def test_published_network_data(request):
    """ Test endpoint that always checks the access token. """
    return create_published_network_data_response(request)
