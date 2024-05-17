"""
SPDX-License-Identifier: Apache License 2.0

Copyright 2023 GRENMap Authors

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

Synopsis: Django models for the hierarchical database polling sources
    directly below this node in the hierarchy.
"""

import logging
import requests
from json.decoder import JSONDecodeError

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.conf import settings
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from base_app.models.app_configurations import TOKEN_LENGTH
from base_app.serializers import EXPORTING_ERRORS
from base_app.utils.access_control import is_in_production_mode
from polling.exceptions import SourcePollError


log = logging.getLogger()


class PollingSource(models.Model):
    """
    A single HTTP data source directly below this node in the
    hierarchical database tree.
    """

    # The displayed name of the data source
    name = models.CharField(
        max_length=140,
        unique=True,
        verbose_name=_('name'),
        help_text=_('An easy to remember name for this connection.'
                    ' i.e. The organization this is for.')
    )

    protocol = models.CharField(
        max_length=5, default='https',
        choices=[
            ('https', 'HTTPS'),
            ('http', 'HTTP'),
        ],
        verbose_name=_('protocol'),
    )
    hostname = models.CharField(
        max_length=255, null=False,
        verbose_name=_('host name'),
    )

    port = models.PositiveIntegerField(
        default=443,
        verbose_name=_('port'),
    )

    path = models.CharField(
        max_length=255,
        validators=[RegexValidator(r'(\w+/)+')],
        null=False,
        blank=True,
        verbose_name=_('path'),
        help_text=_('The path to the GRENML DB node at this URL.'
                    ' Must end with a forward slash. (/)')
    )

    active = models.BooleanField(
        default=True, null=False,
        verbose_name=_('active'),
    )

    token = models.CharField(
        max_length=TOKEN_LENGTH,
        null=True,
        blank=True,
        help_text=_('Access token provided by the peer node adminsitrator.'),
        verbose_name=_('Token')
    )

    # Question: Should there be an SSL Certificate field here for
    #  easier HTTPS authentication?

    # Set the default paths to be used when checking the status
    # and the polling endpoint of a polling source.
    # Set here for easy access and modification.
    _status_path = models.CharField(
        max_length=255, default='status', editable=False,
        verbose_name=_('status path'),
    )
    _polling_path = models.CharField(
        max_length=255, default='grenml_export', editable=False,
        verbose_name=_('polling path'),
    )

    objects = models.Manager()

    @property
    def url(self):
        # Do not use HTTP protocol or a port number different from 443
        # if the node is not in development mode.
        protocol = self.protocol
        port = self.port
        if is_in_production_mode():
            protocol = 'HTTPS'
            port = '443'

        return f'{protocol}://{self.hostname}:{port}/{self.path}'

    @property
    def status_url(self):
        return f'{self.url}{self._status_path}/'

    @property
    def polling_url(self):
        return f'{self.url}{self._polling_path}/'

    @property
    def verify_certificate(self):
        # Check if the node is in development mode
        # Verify certificate based on the mode.
        if is_in_production_mode():
            return True
        else:
            return False

    def poll(self):
        """
        Performs the polling action of contacting the host URL,
        receives the GRENML data, and passes it along in text form.
        """
        try:
            log.info(f'Start polling: {self.polling_url}')
            r = requests.get(
                self.polling_url,
                headers={
                    'Authorization': 'Bearer %s' % self.token
                },
                verify=self.verify_certificate,
                timeout=settings.REQUEST_TIMEOUT,
            )

        # Includes requests.ConnectionError for unavailable URL
        except requests.RequestException as e:
            error_message = _(
                # Translators: first {} is an error message, second is a URL (network address)  # noqa
                'Connection error {} with polling source [{}]'
            ).format(e.response, self.polling_url)
            log.error(error_message)
            raise SourcePollError(error_message, e.response)

        if r.status_code != HTTP_200_OK:
            self.handle_polling_error(r, self.polling_url)

        return r.text

    def handle_polling_error(self, response, polling_url):
        """
        Helper function that raises a SourcePollError containing the UI
        message associated to the error code in the response when a
        polling request fails.
        """
        status = response.status_code
        log.error(f'Error code {status} polling {polling_url}.')
        if status == HTTP_403_FORBIDDEN:
            request_error = _('Access denied. Token missing or invalid.')
        else:
            try:
                error_type = response.json()['error_type']
            except JSONDecodeError:
                log.exception('handle_polling_error: no error type in response')
                error_type = 'Exception'
            log.error(f'Error type: {error_type}')
            # use the error type to get an error message
            request_error = EXPORTING_ERRORS.get(error_type)
        raise SourcePollError(request_error, status)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('GRENML Polling Source')
        verbose_name_plural = _('GRENML Polling Sources')
