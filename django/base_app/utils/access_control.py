"""
Copyright 2021 GRENMap Authors

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

from base_app.models import Token


log = logging.getLogger()


def is_in_production_mode():
    """
    Returns True if the application is in production mode.

    Relies on the DEVELOPMENT environment variable, which is normally
    defined in one of the files in the "env" directory.
    """
    return os.environ.get('DEVELOPMENT') != '1'


def get_token(request):
    """
    Tries to extract an access token from the request, then searches
    the database for a matching Token record and returns it.

    Returns none:
    - in case the request doesn't have a token;
    - if the token in the request is not stored in the database;
    - if it isn't possible to obtain the token type
      from the request's path;
    - if the request's token type is different from the one
      in the database.
    """
    # obtain the token from the request
    try:
        request_token = request.headers.get('Authorization').split()[1]
    except Exception:
        log.exception('get_token: could not extract token from request')
        return None

    # check that the token exists in the database
    try:
        token = Token.objects.get(token=request_token)
    except Token.DoesNotExist:
        log.warning('get_token: token %s not found', request_token)
        return None

    # obtain the token type from the request
    try:
        token_type = request.META['PATH_INFO'].split('/')[1]
    except Exception:
        log.exception('get_token: could not obtain token type')
        return None

    log.debug('get_token: checking token: %s for app: %s', request_token, token_type)

    # published_network_data shares the same token as grenml_export
    if token_type == 'published_network_data':
        token_type = 'grenml_export'

    # check that the token was created for the app
    if token.token_type != token_type:
        log.warning(
            'get_token: token %s has type different from type %s in request',
            request_token,
            token_type,
        )
        return None

    return token


def allow_request(request, access_control_enabled):
    """
    Determines if a request should be accepted or not, based on
    the presence and value of an access token header.

    The access_control_enabled function doesn't take any parameters
    and returns a boolean. When its return value is True, the token
    check happens.
    """
    if access_control_enabled():
        return bool(get_token(request))
    else:
        # access control is disabled, accept the request
        log.info('allow_request: access control is disabled')
        return True
