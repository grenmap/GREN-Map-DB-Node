"""
Copyright 2022 GRENMap Authors

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
import os
from io import BytesIO

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from base_app.constants import IMPORT_TOKEN_MESSAGE
from base_app.serializers import AccessDeniedSerializer, GRENMLImportSerializer
from base_app.utils.access_control import get_token
from base_app.utils.decorators import test_only
from grenml_import.models import ImportFile, file_name as make_file_name
from grenml_import.serializers import ImportFileSerializer
from grenml_import.importer import GRENMLImporter
from network_topology.models.topology import Topology
from network_topology.exceptions import MoreThanOneMainTopologyError

logger = logging.getLogger(__name__)


@extend_schema(
    description=_(
        # Translators: <br> is an HTML tag that inserts a new line. Please keep both at the end of the message.  # noqa
        'Use this endpoint to upload a GRENML file. <br> <br> '
    ) + IMPORT_TOKEN_MESSAGE,
    auth=[{'import token': []}],
    tags=[],
    request={'multipart/form-data': GRENMLImportSerializer},
    responses={
        201: None,
        ('403', 'application/json'): AccessDeniedSerializer,
    }
)
@api_view(['POST'])
def post_xml_file(request):
    """
    Use this API endpoint to upload xml file to gren map db node
    headers={'Authorization': 'Bearer 4hT6YjO6oYmsdB0o77gSNZCz111'}
    files={'file': your xml file}
    """
    token = get_token(request)
    if not token:
        raise PermissionDenied('Failed access control check')

    try:
        logger.info('Get POST request to upload file')
        filename = request.FILES['file'].name
        if not filename.endswith(('xlsx', 'xml')):
            return Response(
                f'Uploaded file [{filename}] does not have a valid extension.',
                status=status.HTTP_406_NOT_ACCEPTABLE
            )
        file_contents = request.FILES['file'].read().decode('utf-8')
    except Exception:
        logger.exception('Failed to read the uploaded file: ')
        return Response(
            'Failed to read the uploaded file',
            status=status.HTTP_400_BAD_REQUEST
        )

    file_name = request.FILES['file'].name
    client_name = token.client_name

    model = ImportFile()

    # determine the selected topology
    parent_topology_id = request.data.get('parent_topology_id')

    if bool(parent_topology_id):
        try:
            model.parent_topology = Topology.objects.get(id=parent_topology_id)
        except Topology.DoesNotExist:
            return Response(
                'Topology with id {} does not exist'.format(parent_topology_id),
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        try:
            model.parent_topology = Topology.objects.get_main_topology()
        except MoreThanOneMainTopologyError:
            model.parent_topology = None
        logger.info('post_xml_file: parent_topology_id not given, using root')

    model.topology_name = request.data.get('topology_name')

    import_file_contents(model, file_name, file_contents, client_name)
    logger.info('received file: %s - token client name: %s', file_name, client_name)
    return Response(status=status.HTTP_201_CREATED)


def import_file_contents(model, file_name, file_contents, client_name):
    """
    Takes the contents of a file, received by the server in a multipart
    request, and saves it on the database.
    """
    filepath = os.path.join(
        settings.MEDIA_ROOT,
        make_file_name(None, file_name),
    )
    model.source = ImportFile.API_SOURCE
    model.file.save(filepath, ContentFile(file_contents))
    model.token_client_name = client_name
    model.save()


@test_only
@api_view(['POST'])
def test_post_xml_data(request):
    """
    Use this test API endpoint to upload xml data in JSON format
    to gren map db node
    """
    importer = GRENMLImporter()
    response_message = importer.from_stream(BytesIO(request.data.encode()))

    if 'Errors' in response_message:
        return Response(response_message, status=status.HTTP_400_BAD_REQUEST)

    return Response(response_message, status=status.HTTP_201_CREATED)


@test_only
@api_view(['DELETE', 'GET'])
def test_import_files(request):
    """
    Test endpoint to fetch and delete (depending on the HTTP method)
    all ImportFile records.
    """
    if request.method == 'GET':
        serializer = ImportFileSerializer(ImportFile.objects.all(), many=True)
        entries = serializer.data
    elif request.method == 'DELETE':
        for entry in ImportFile.objects.all():
            entry.delete()
        entries = []
    return Response(
        status=status.HTTP_200_OK,
        data=entries,
    )
