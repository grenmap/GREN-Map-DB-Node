"""
Copyright 2026 GRENMap Authors

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
from urllib.parse import urlparse

from django.utils.translation import gettext as _
from django.forms import ValidationError

from base_app.utils.custom_configuration import CustomConfiguration


class RepositorySyncEnabledSetting(CustomConfiguration):
    name = 'GRENML_REPOSITORY_SYNC_ENABLED'
    display_name = 'GRENML Repository Sync Enabled'
    default_value = 'False'
    description = _(
        # Translators: 'True' and 'False' should remain in English, do not translate  # noqa
        "Value must be 'True' or 'False' (Case sensitive)"
    )

    def clean(self, value):
        if value == 'True' or value == 'False':
            return
        raise ValidationError(self.description, code='invalid')


class RepositorySyncURLSetting(CustomConfiguration):
    name = 'GRENML_REPOSITORY_SYNC_URL'
    display_name = 'GRENML Repository Sync URL'
    default_value = (
        'https://raw.githubusercontent.com/grenmap/GRENML-Repository/main/RENMAP/topologies.xml'
    )
    description = _(
        'URL of the GRENML file to import whenever it changes (http or https)'
    )

    def clean(self, value):
        parsed = urlparse(value)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValidationError(self.description, code='invalid')


class RepositorySyncIntervalSetting(CustomConfiguration):
    name = 'GRENML_REPOSITORY_SYNC_INTERVAL'
    display_name = 'GRENML Repository Sync Interval'
    default_value = '10'
    description = _(
        'How often, in minutes, to check the GRENML file for changes (a whole number, 1 or more)'
    )

    def clean(self, value):
        if not value.isdigit() or int(value) < 1:
            raise ValidationError(self.description, code='invalid')

    def post_save(self, value):
        # Imported here: the scheduling module reads the configuration
        # table, which imports this module while it is being loaded.
        from repository_sync.scheduling import schedule_sync
        schedule_sync(int(value))
