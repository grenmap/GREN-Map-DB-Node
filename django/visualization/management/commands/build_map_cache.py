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

Synopsis: This command should be run when the django application is
started to create/update the polling task on the polling
scheduler service
"""

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from visualization.cache import save_initial_map_data_for_all_entities


class Command(BaseCommand):
    help = _('Build Redis Cache For Visualization')

    def handle(self, *args, **options):
        save_initial_map_data_for_all_entities()
