"""
This file contains the django models for the various setting that can be
configured for this application
"""

import logging
import random
import string

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from base_app.settings import INSTALLED_APPS, TOKEN_TYPES
import importlib
import inspect
from django.db.models.signals import post_save
from django.dispatch import receiver
from base_app.utils.custom_configuration import CustomConfiguration

# A dict of setting names to setting objects
CONFIGURATION_DEFINITIONS = {}

# Access token length.
TOKEN_LENGTH = 32

log = logging.getLogger()


# Loop through all apps and load in the settings
# Import errors are ignored because some apps may not define settings
for app_name in INSTALLED_APPS:
    try:
        temp = f'{app_name}.app_configurations'
        module_members = inspect.getmembers(
            importlib.import_module(
                temp,
            )
        )
        for name, obj in module_members:
            if inspect.isclass(obj):
                if not obj == CustomConfiguration and issubclass(obj, CustomConfiguration):
                    setting = obj()
                    CONFIGURATION_DEFINITIONS[setting.name] = setting

    except ModuleNotFoundError:
        pass


class AppConfiguration(models.Model):
    """
    The configurable settings for the application
    """

    name = models.CharField(
        max_length=140, null=False, blank=False, unique=True, primary_key=True,
        verbose_name=_('name'),
    )

    display_name = models.CharField(
        max_length=140, null=False, blank=False,
        verbose_name=_('display name')
    )

    value = models.CharField(
        max_length=500, null=False, blank=True,
        verbose_name=_('value')
    )

    description = models.CharField(
        max_length=500, null=True, blank=False,
        verbose_name=_('description')
    )

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name = _('App Configuration Setting')
        verbose_name_plural = _('App Configuration Settings')


@receiver(post_save, sender=AppConfiguration)
def post_save(instance, **kwargs):
    """
    After the model is saved, this will trigger
    any registered setting save hooks
    """
    if instance.name in CONFIGURATION_DEFINITIONS:
        CONFIGURATION_DEFINITIONS[instance.name].post_save(instance.value)


class Token(models.Model):
    """ Access token for API requests."""

    client_name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_('This identifies the client which will be using this token.'),
        verbose_name=_('client name')
    )
    token = models.CharField(
        max_length=TOKEN_LENGTH,
        null=False,
        blank=False,
        unique=True,
        help_text=_(
            "The access token, a random string. "
            "Use the regenerate button to populate this field in case it is empty. "
            "Send it to the peer's administrator "
            "to have this node accept the peer's requests."
        ),
        verbose_name=_('Token')
    )
    token_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=False,
        choices=TOKEN_TYPES,
        default='grenml_export',
        verbose_name=_('token type')
    )

    def __str__(self):
        return self.client_name

    def regenerate_token(self):
        """ Re-populates the token with a random string. """

        charset_string = string.ascii_uppercase + string.ascii_lowercase + string.digits
        random_string = ''.join([
            random.SystemRandom().choice(charset_string)
            for _ in range(TOKEN_LENGTH)
        ])
        log.info('regenerate_token: updated token for %s', self.client_name)
        self.token = random_string
        self.save()

    class Meta:
        verbose_name = _('Token')
        verbose_name_plural = _('Tokens')


def create_dynamic_form():
    """
    This uses the CustomConfiguration objects defined across
    the Django apps to create a class derived from ModelForm
    during runtime. The admin page to edit app settings uses
    the class to validate user input.
    """
    def clean_method(form):
        clean_data = super(DynamicAppConfigurationForm, form).clean()

        # look up the CustomConfiguration by the setting name then
        # call its clean method
        name = form.instance.name
        value = form.data['value']
        clean_value = CONFIGURATION_DEFINITIONS[name].clean(value)

        # some CustomConfiguration classes return a value, some don't
        if clean_value is not None:
            clean_data['value'] = clean_value

        return clean_data

    form_meta_class = type(
        'Meta',
        (),
        {'model': AppConfiguration, 'fields': ['value']},
    )

    form_class = type(
        'DynamicAppConfigurationForm',
        (forms.ModelForm,),
        {'Meta': form_meta_class, 'clean': clean_method},
    )
    return form_class


DynamicAppConfigurationForm = create_dynamic_form()
