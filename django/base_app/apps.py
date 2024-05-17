"""
This file contains app configuration and special hooks for when django
is finished initializing
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BaseAppConfig(AppConfig):

    name = 'base_app'
    verbose_name = _('Base App')
