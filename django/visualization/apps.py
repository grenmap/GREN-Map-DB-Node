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

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

from .cache import post_save_connect


INITIAL_UI_STRINGS = [
    ('link_details', 'Link Details'),
    ('connected_to', 'Connected to:'),
    ('managed_by', 'Managed by:'),
    ('close', 'Close'),
    # Split in two (rather than one "Owned by {n} institutions" string)
    # so the institution count never sits inside machine-translated
    # text, where a placeholder could get mistranslated or reordered.
    ('owned_by', 'Owned by'),
    ('institutions_plural', 'institutions'),
]


def seed_ui_strings(sender, **kwargs):
    """
    Ensures the fixed map interface vocabulary exists. Connected to
    post_migrate (rather than done as a data migration) because the
    dev entrypoint runs "manage.py flush" on every container start,
    which clears table data without unmarking migrations as applied
    -- a data migration's RunPython would then never run again.
    post_migrate fires after every "migrate" call, including the one
    that follows that flush, so this survives it.
    """
    from .models import UIString
    for key, text in INITIAL_UI_STRINGS:
        UIString.objects.get_or_create(key=key, defaults={'text': text})


class VisualizationConfig(AppConfig):
    name = 'visualization'
    verbose_name = _('GREN Map Visualization')

    def ready(self):
        super().ready()
        post_save_connect()
        post_migrate.connect(seed_ui_strings, sender=self)
