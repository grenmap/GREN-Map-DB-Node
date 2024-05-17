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

This file contains a wrapper view for GraphQL, allowing the application
to dynamically enable/disable the graphql endpoint for visualization
"""

import json
import logging
import re

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from base_app.models import AppConfiguration
from base_app.utils.decorators import test_only
from base_app.settings import ALLOWED_HOSTS

from visualization.app_configurations import (
    InitialCoordinatesSetting,
    InitialMapZoomSetting,
    VisualizationEnabledSetting,
    VisualizationCachedSetting,
)
from visualization.cache import get_initial_map_data
from visualization.models import VisualizationAllowedOrigin
from visualization.schema import schema
from visualization.utils import visualization

logger = logging.getLogger()


def _cors_headers(request, response=HttpResponse('')):
    """
    Applies CORS headers as well as other basic headers to the response
    going to the client
    """
    origin = request.headers.get('origin', None)
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS, POST'
    response['Access-Control-Allow-Origin'] = origin
    return response


def check_visualization_request(request):
    """
    Verifies that visualization is enabled and that the client
    is allowed to request visualization data.
    """
    # Check if the request origin is allowed
    origin = request.headers.get('origin', None)
    logger.debug('visualization request from origin: %s' % origin)
    if origin is not None:
        try:
            VisualizationAllowedOrigin.objects.get(origin=origin, active=True)
        except ObjectDoesNotExist:
            origin_domain = origin.split(":")[1].replace('//', '')
            if (origin_domain not in ALLOWED_HOSTS) and ('*' not in ALLOWED_HOSTS):
                logger.warn('Origin: %s is not allowed for visualization' % origin)
                return _cors_headers(
                    request,
                    response=HttpResponse('', status=status.HTTP_401_UNAUTHORIZED)
                )

    if AppConfiguration.objects.get(
        name='GREN_MAP_VISUALIZATION_ENABLED'
    ).value == 'False':
        response = JsonResponse({
            "errors": [
                {"message": _("Visualization is disabled")}
            ],
            "data": {}
        })
        return _cors_headers(request, response)

    return None


def fresh_graphql_response(request):
    """
    Calls graphene-django's GraphQLView to run query on the database.
    Returns an HTTP response.
    """
    logger.debug('Get fresh_graphql_response')
    response = GraphQLView.as_view(graphiql=True, schema=schema)(request)
    return _cors_headers(request, response)


@csrf_exempt
def visualization_graphql_api(request):
    """
    This view provides the graphql functionality,
    plus the features to enable/disable it.

    The GraphQL query request for single network element is like:
    '{\n node(id: "591d15151ec0181055287fee53cb78fe8c4a43") ...'

    The GraphQL query request for all of the network elements(nodes,
    links, institutions) is like:
    '{\n  nodes {\n    id\n    name\n    shortName\n ...'
    """
    if request.method == 'OPTIONS':
        return _cors_headers(request)

    if request.method == "GET" or request.method == "POST":
        response = check_visualization_request(request)
        if response is not None:
            return response

        # Return cached data for request of nodes/links/institutions
        # when cache is enabled
        try:
            body = json.loads(request.body)
            entity_line = body['query'].split('\n')[1].strip()
            elements_matched = re.match('([a-z]+) {', entity_line)
            if elements_matched:
                cache_enabled = AppConfiguration.objects.get(name=VisualizationCachedSetting.name)
                if cache_enabled.value == 'True':
                    entity = elements_matched[1]
                    logger.info(f'Get cached data for: {entity}')
                    map_data = get_initial_map_data(entity)
                    return _cors_headers(
                        request,
                        HttpResponse(map_data, status=status.HTTP_200_OK),
                    )
        except Exception:
            logger.exception(
                'Wrong formatting in request data. '
                f'Get request body: {body}'
            )

        # Return fresh data for all of the other requests
        return fresh_graphql_response(request)

    else:
        return HttpResponse(
            'Request method is not allowed.', status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def initial_coordinates_setting(request):
    """
    Report the Initial coordinates for the map positioning
    """
    setting = AppConfiguration.objects.get(name=InitialCoordinatesSetting.name)
    coordinates = visualization.extract_coordinates(setting.value)
    return _cors_headers(request, response=JsonResponse(coordinates))


@api_view(['GET'])
def initial_map_zoom_setting(request):
    """
    Report the Initial coordinates for the map positioning
    """
    setting = AppConfiguration.objects.get(name=InitialMapZoomSetting.name)
    zoom = float(setting.value)
    return _cors_headers(request, response=JsonResponse({'zoom': zoom}))


def fullscreen_map(request):
    """
    Displays the fullscreen map if it is enabled in settings.
    If not, this redirects to the login/admin page
    """
    enabled = AppConfiguration.objects.get(name=VisualizationEnabledSetting.name)
    if enabled.value == 'False':
        return redirect('/admin/')
    return render(request, 'entities/visualization_fullscreen.html')


@test_only
@api_view(['GET'])
def visualization_enabled_setting(request):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Reports the current enabled state of automatic polling:
    "True" or "False"
    """
    setting = AppConfiguration.objects.get(name=VisualizationEnabledSetting.name)
    return Response(setting.value)


@test_only
@api_view(['PUT'])
def visualization_enabled_setting_toggle(request, enable=0):
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
    setting = AppConfiguration.objects.get(name=VisualizationEnabledSetting.name)
    setting.value = enabled_setting_value
    setting.save()
    return Response(setting.value)


@test_only
@api_view(['POST'])
def visualization_allow_origins(request, name=None):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    Example POST JSON input:
    {
        "name": "test",
        "origin": "http://localhost:4200",
        "active": "True" or ""
    }
    """
    params = request.data
    name = params['name']
    origin = params['origin']
    active = params['active']
    if name == '' or origin == '':
        response = Response(
            'JSON input must contain non-null all fields.',
            status=status.HTTP_400_BAD_REQUEST,
        )
    else:
        VisualizationAllowedOrigin.objects.create(
            name=name,
            origin=origin,
            active=bool(active)
        )
        response = Response('', status=status.HTTP_201_CREATED)
    return response


@test_only
@api_view(['DELETE'])
def visualization_allow_origin(request, name=None):
    """
    This REST API endpoint is intended as a testing hook only.  It has
    not been rigorously constructed or tested, and should not be used
    in production, for risk of undefined results.

    This REST API will try to remove the allow origin base on
    the name field.
    """
    if name is None:
        response = Response(
            'Name can not be None.',
            status=status.HTTP_400_BAD_REQUEST,
        )
    else:
        try:
            allow_origin = VisualizationAllowedOrigin.objects.get(name=name)
            allow_origin.delete()
            response = Response('', status=status.HTTP_204_NO_CONTENT)
        except VisualizationAllowedOrigin.DoesNotExist:
            response = Response(
                f'Unable to find the origin with name: {name}',
                status=status.HTTP_400_BAD_REQUEST,
            )
    return response
