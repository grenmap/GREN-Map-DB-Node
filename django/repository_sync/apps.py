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
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


def register_sync_schedule(sender, **kwargs):
    """
    Puts the sync job on the scheduler. Connected to post_migrate
    because the dev entrypoint runs "manage.py flush" on every
    container start, which wipes the Schedule table; post_migrate fires
    after the "migrate" that follows it (see visualization/apps.py).
    """
    from .scheduling import schedule_sync
    schedule_sync()


class RepositorySyncConfig(AppConfig):
    name = 'repository_sync'
    verbose_name = _('GRENML Repository Sync')
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        super().ready()
        post_migrate.connect(register_sync_schedule, sender=self)
