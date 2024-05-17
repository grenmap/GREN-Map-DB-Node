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

Synopsis: Test file for the setting validators for the polling app
"""

from polling.app_configurations import PollingIntervalSetting
from polling.app_configurations import PollingEnabledSetting
import pytest
from django.forms import ValidationError


class TestConfigurationValidators:

    @pytest.fixture
    def polling_interval(self):
        return PollingIntervalSetting()

    @pytest.fixture
    def polling_enabled(self):
        return PollingEnabledSetting()

    def test_invalid_cron(self, polling_interval):
        """
        Should return error strings for invalid cron strings
        """
        with pytest.raises(ValidationError):
            polling_interval.clean('a a a b b *')

        with pytest.raises(ValidationError):
            polling_interval.clean('@every 7z')

        """
        The config value of '@every 4h' was valid when DKron was used
        as the scheduler. The format is not supported by cronitor.
        """
        with pytest.raises(ValidationError):
            polling_interval.clean('@every 4h')

    def test_valid_cron(self, polling_interval):
        """
        Should successfully validate the valid cron strings
        """
        polling_interval.clean('* * * * * *')
        polling_interval.clean('5 * * * * *')
        polling_interval.clean('R */4 * * *')

    def test_invalid_polling_enabled(self, polling_enabled):
        with pytest.raises(ValidationError):
            polling_enabled.clean('true')
        with pytest.raises(ValidationError):
            polling_enabled.clean('false')
        with pytest.raises(ValidationError):
            polling_enabled.clean('TRUE')
        with pytest.raises(ValidationError):
            polling_enabled.clean('FALSE')
        with pytest.raises(ValidationError):
            polling_enabled.clean('asdas')
        with pytest.raises(ValidationError):
            polling_enabled.clean('Falseasdasd')
        with pytest.raises(ValidationError):
            polling_enabled.clean('Trueasdasd')

    def test_valid_polling_enabled(self, polling_enabled):
        polling_enabled.clean('True')
        polling_enabled.clean('False')
