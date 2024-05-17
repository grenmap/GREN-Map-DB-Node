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
"""
from croniter import croniter

from django.utils.translation import gettext as _
from django.forms import ValidationError

from base_app.utils.custom_configuration import CustomConfiguration
from polling.utils.schedule_polling import schedule_job


class PollingIntervalSetting(CustomConfiguration):
    name = 'GRENML_POLLING_INTERVAL'
    display_name = 'GRENML Polling Interval'

    """Poll every 4 hours, starting on a random minute"""
    default_value = 'R */4 * * *'

    description = _(
        'Schedule value must use croniter crontab format '
        '(See https://github.com/kiorky/croniter)'
    )

    def clean(self, value):
        """
        Checks that the format is what is expected by croniter

        See https://github.com/kiorky/croniter
        """
        if not croniter.is_valid(value):
            raise ValidationError(self.description, code='invalid')

    def post_save(self, value):
        """
        Triggered when a polling interval is saved. Calls the utility
        function for synchronising the remote scheduler with the local
        configuration
        """
        schedule_job(value)


class PollingEnabledSetting(CustomConfiguration):
    name = 'GRENML_POLLING_ENABLED'
    display_name = 'GRENML Polling Enabled'
    default_value = 'True'
    description = _(
        # Translators: 'True' and 'False' should remain in English, do not translate  # noqa
        "Value must be 'True' or 'False' (Case sensitive)"
    )

    def clean(self, value):
        """
        Checks that the value is either true or false
        """
        if value == 'True' or value == 'False':
            return
        raise ValidationError(self.description, code='invalid')


class PollingDataSupplyTypeSetting(CustomConfiguration):

    name = 'GRENML_POLLING_DATA_SUPPLY_TYPE'
    display_name = 'GRENML Polling Data Supply Type'
    default_value = 'Live'
    description = _(
        # Translators: 'Live' and 'Published' should remain in English, do not translate  # noqa
        "Value must be 'Live' or 'Published' (Case sensitive)"
    )

    def clean(self, value):
        """
        Checks that the value is either Live or Published_Data
        """
        if value == 'Live' or value == 'Published':
            return
        raise ValidationError(self.description, code='invalid')
