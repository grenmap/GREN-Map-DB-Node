"""
SPDX-License-Identifier: Apache License 2.0

Copyright 2022 GRENMap Authors

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

Synopsis: This file contains the fim login/logout method
"""

from django.utils.translation import gettext as _
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from fim.models.rs_identity import RSIdentity
import logging

log = logging.getLogger(__name__)

# Shibboleth Attributes
EPPN = 'eppn'
EMAIL = 'mail'
DISPLAY_NAME = 'displayName'
FIRST_NAME = 'givenName'
LAST_NAME = 'sn'

# First value in tuple indicates requirement
# Second value is the related field name in RS_Identity model
SHIB_ATTRIBUTE_MAP = {
    EPPN: (True, 'eppn'),
    EMAIL: (False, 'email'),
    DISPLAY_NAME: (False, 'display_name'),
    FIRST_NAME: (False, 'first_name'),
    LAST_NAME: (False, 'last_name'),
}

SHIB_LOGOUT_URL = '/Shibboleth.sso/Logout?%s'
HTTP_PREFIX = 'HTTP_X_FORWARDED_'


class FIMAttributeError(Exception):
    def __init__(self, err_msg, attributes={}):
        err_msg = err_msg
        attributes = attributes


def parse_shib_attributes(request):
    """
    Checks for required attributes and normalizes the others into
    a dictionary using constants as keys.
    Returns a tuple: (shib_attributes, error)
    """
    shib_attrs = {}
    error = False

    # Normalize shib attributes into a dictionary,
    # checking for any basic required attributes
    shib_attr_log_message = ''
    for attribute, field in SHIB_ATTRIBUTE_MAP.items():
        required = field[0]
        meta_key = HTTP_PREFIX + attribute.upper()
        values = request.META.get(meta_key, None)
        value = None
        if values:
            # If the attribute release contains multiple values,
            # discard all but the first
            shib_attr_log_message += f' {attribute}: [{values}]'
            try:
                value = values.split(';')[0]
            except:  # noqa: E722
                value = values

        shib_attrs[attribute] = value
        if not value:
            if required:
                error = True
                log.info(f'Missing required attribute: {attribute}')

    log.info(f'Parsed Shibboleth attributes: {shib_attr_log_message}')

    return shib_attrs, error


def normalize(request, attributes):
    """
    Converts a set of FIM (Shibboleth) attributes into a Django user.
    Returns the User if normalization succeeds.
    """
    # Get the user's username, as provided by Shibboleth
    eppn = attributes.get(EPPN, None)
    log.debug(f'Normalizing FIM credentials ({eppn} with Django User')

    # First store/retrieve eppn; it will be linked to a django user
    try:
        rs_identity = RSIdentity.objects.get(eppn__iexact=eppn)
    except ObjectDoesNotExist:
        log.debug('Create a new Django User for EPPN: %s' % eppn)
        rs_identity = RSIdentity.objects.create(eppn=eppn)
    # Update attributes
    for attribute, field in SHIB_ATTRIBUTE_MAP.items():
        if attribute != EPPN:
            setattr(
                rs_identity,
                field[1],
                attributes.get(attribute) if attributes.get(attribute) else ''
            )
    rs_identity.save()
    rs_identity = RSIdentity.objects.get(eppn__iexact=eppn)
    return rs_identity.user


def fim_login(request, redirect_url='/'):
    """
    Begins a Django session based on valid FIM/Shibboleth attributes
    linked to a User.
    """
    # If there is no Shibboleth session,
    # assume the login excursion has not been completed
    attributes, attr_error = parse_shib_attributes(request)
    if not attributes or attr_error:
        log.warning('Insufficient attributes for login attempt.')
        message = _('Something has gone wrong with your FIM identity. '
                    'Please contact the site administrator for \
                    further assistance.')
        messages.error(request, message)
        return HttpResponseRedirect(redirect_url)

    try:
        user = normalize(request, attributes)
    except FIMAttributeError:
        log.warning('Failing login due to FIM attribute error.')
        return HttpResponseRedirect(redirect_url)
    except Exception as err:  # noqa: E722
        log.warning('Failing login due to Django User normalization error: %s' % err)
        return HttpResponseRedirect(redirect_url)

    # Django login
    login(request, user)
    log.info(f'user {user.username} with eppn \
        {attributes[EPPN]} logged in via FIM/Shibboleth.')

    # Let the user know they successfully logged in
    message = _(
        # Translators: do not translate user.first_name and user.last_name  # noqa
        'Welcome %(first_name)s %(last_name)s. You are now logged in.'
    ) % {'first_name': user.first_name, 'last_name': user.last_name}
    messages.info(request, message)

    return HttpResponseRedirect(redirect_url)


def fim_logout(request, redirect_url='/'):
    """
    End the user's Django session.
    """
    HttpResponseRedirect(SHIB_LOGOUT_URL)
    if request.user.is_authenticated:
        # Log out of Django
        logout(request)
        log.info(f'User {request.user.username} logged out.')
        message = _(
            'You are logged out.  Your identity credentials may '
            'still be stored in your browser; if you are using a public computer, '
            'please fully exit your browser to completely log out.')
        messages.info(request, message)

    return HttpResponseRedirect(redirect_url)
