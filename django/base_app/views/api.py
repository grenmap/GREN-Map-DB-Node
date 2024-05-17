"""
The initial API file for the GREN map
"""

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from django.db import DEFAULT_DB_ALIAS
from django.core.management import call_command
from io import StringIO
import json
from base_app.models.app_configurations import Token
from base_app.utils.decorators import test_only
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView

import logging
logger = logging.getLogger()


@extend_schema(
    description='Health check endpoint.',
    auth=[],
    tags=[],
    responses={'200': None},
)
@api_view(['GET'])
def status_api(request):
    return Response(
        status=HTTP_200_OK
    )


# #251 SLATED FOR DELETION:
@api_view(['POST'])
def collect_data(request):
    return Response(
        data={
            'message': 'This end point is a stand in for the GRENML endpoint'
        },
        status=HTTP_200_OK
    )


# #251 SLATED FOR DELETION:
@api_view(['POST'])
def import_data(request):
    if request.POST is None:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR)
    # #251 old deprecated line: GrenmlImport().import_data(request.POST)
    raise NotImplementedError('base_app.views.api.import_data deprecated!')
    return Response(
        data={
            'message': 'This end point is a stand in for the GRENML import endpoint'
        },
        status=HTTP_200_OK
    )


def openapi_schema(request):
    """
    Intercepts the OpenAPI schema response to insert a server URL,
    obtained from the request.
    """
    schema_view = SpectacularAPIView.as_view()
    response = schema_view(request)

    if 'servers' not in response.data:
        logger.info(
            "openapi_schema: 'servers' missing in schema, "
            'it will not be possible to try endpoints with swagger-ui. '
            'Check SPECTACULAR_SETTINGS in base_app.settings.'
        )
        return response

    servers = response.data['servers']
    if len(servers) == 0:
        logger.info(
            "openapi_schema: no servers configured, "
            'it will not be possible to try endpoints with swagger-ui. '
            'Check SPECTACULAR_SETTINGS in base_app.settings.'
        )
        return response

    # It would not work if we used request.scheme, because django
    # is behind shibolleth/apache.
    # Request.scheme is 'http' instead of 'https'
    # and request.get_port() is 8080 instead of 8443.
    request_scheme = 'https'

    servers[0]['url'] = request_scheme + '://' + request.get_host()

    return response


@test_only
@api_view(['POST'])
def flush_db(request):
    db_name = DEFAULT_DB_ALIAS
    # Flush the database
    call_command(
        'flush', verbosity=0, interactive=False,
        database=db_name, reset_sequences=False,
        allow_cascade=False,
        inhibit_post_migrate=False
    )
    return Response(
        data={
            'message': 'Database flushed'
        },
        status=HTTP_200_OK
    )


@test_only
@api_view(['POST'])
def create_superuser(request):
    test_user = json.loads(request.body.decode('utf-8'))
    if test_user['username'] is not None and test_user['password'] is not None:
        if test_user['email']:
            User.objects.create_superuser(
                test_user['username'],
                test_user['email'],
                test_user['password']
            )
        else:
            User.objects.create_superuser(
                test_user['username'],
                'test@example.com',
                test_user['password']
            )
        return Response(
            data={
                'message': f'User {test_user["username"]} is created'
            },
            status=HTTP_200_OK
        )
    else:
        return Response(
            data={
                'message': 'Incorrect test data provided'
            },
            status=HTTP_400_BAD_REQUEST
        )


@test_only
@api_view(['POST'])
def load_fixture(request):
    body = json.loads(request.body.decode('utf-8'))
    if 'fixture' in body:
        out = StringIO()
        call_command(
            'loaddata', body['fixture'],
            stdout=out
        )
        return Response(
            data={
                'message': out.getvalue()
            },
            status=HTTP_200_OK
        )
    else:
        return Response(
            data={
                'message': "Fixture name not provided"
            },
            status=HTTP_400_BAD_REQUEST
        )


@test_only
@api_view(['POST'])
def create_token(request):
    """
    Test endpoint that creates an access token.

    Example curl command to use the endpoint:
    curl -X POST -d '{"client_name": "test-node", "token": "1234"}' \
    localhost/test/token/
    """
    payload = json.loads(request.body.decode('utf-8'))
    Token.objects.create(
        client_name=payload['client_name'],
        token=payload['token'],
        token_type=payload['token_type'],
    )
    return Response(status=HTTP_200_OK)
