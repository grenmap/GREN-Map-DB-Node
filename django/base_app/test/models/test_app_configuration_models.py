"""
Test file for the Application Settings model
"""

import pytest
from base_app.models.app_configurations import *
from django.db import IntegrityError


SETTING_NAME_1 = 'TEST_SETTING_1'
SETTING_NAME_2 = 'TEST_SETTING_2'
SETTING_NAME_3 = 'TEST_SETTING_3'
SETTING_VALUE_1 = 'TEST_VALUE_1'
SETTING_VALUE_2 = 'TEST_VALUE_2'
SETTING_VALUE_3 = 'TEST_VALUE_3'


@pytest.mark.django_db(transaction=True)
class TestConfigurationSaving:

    @pytest.fixture
    def app_configurations(self):
        settings = [
            AppConfiguration.objects.create(name=SETTING_NAME_1, value=SETTING_VALUE_1),
            AppConfiguration.objects.create(name=SETTING_NAME_2, value=SETTING_VALUE_2),
        ]
        return settings

    def test_configuration_is_not_created_with_same_name(self, app_configurations):
        """
        Should throw an exception since a setting already exists
        with the given name
        """
        with pytest.raises(IntegrityError):
            AppConfiguration.objects.create(name=SETTING_NAME_1, value=SETTING_VALUE_1)

    def test_unique_configuration_created_no_errors(self, app_configurations):
        """
        Should successfully create a new unique setting
        """
        AppConfiguration.objects.create(name=SETTING_NAME_3, value=SETTING_VALUE_3)

    def test_change_setting_value(self, app_configurations):
        """
        Should successfully modify a settings value
        """
        app_configurations[0].value = 'new_value'
        app_configurations[0].save()
