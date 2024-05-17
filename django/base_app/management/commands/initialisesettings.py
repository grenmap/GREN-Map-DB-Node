"""
This command should be run when the django application is started
to create the default values for settings if they dont exist.
If a setting exists that is not defined by an app, it will be deleted.
"""

from django.core.management.base import BaseCommand
from base_app.models.app_configurations import CONFIGURATION_DEFINITIONS
from base_app.models.app_configurations import AppConfiguration
from django.utils.translation import gettext as _


class Command(BaseCommand):
    help = _('Creates default values for custom app defined settings and cleans unused settings')

    def handle(self, *args, **options):

        # Creates the settings if they dont exist
        for setting in CONFIGURATION_DEFINITIONS:
            AppConfiguration.objects.get_or_create(
                name=CONFIGURATION_DEFINITIONS[setting].name,
                defaults={
                    'value': CONFIGURATION_DEFINITIONS[setting].default_value,
                    'display_name': CONFIGURATION_DEFINITIONS[setting].display_name,
                    'description': CONFIGURATION_DEFINITIONS[setting].description,
                }
            )

        # Makes an easy to search array to be used for checking if
        # a setting should exist
        def filter_tuples(value):
            return value[0]

        # Deletes the unused settings
        setting_names = map(filter_tuples, AppConfiguration.objects.all().values_list('name'))
        for setting in setting_names:
            if setting not in CONFIGURATION_DEFINITIONS:
                AppConfiguration.objects.get(name=setting).delete()
