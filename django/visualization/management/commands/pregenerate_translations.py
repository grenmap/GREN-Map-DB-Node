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
------------------------------------------------------------------------

Synopsis: Pre-generates and caches LibreTranslate translations for all
Institution popup content and UIString map vocabulary, so the first
GraphQL query for each does not have to wait on the translator.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.translation import gettext as _

from network_topology.models import Institution
from visualization.models import UIString
from visualization.translation import (
    ensure_institution_popup_translations,
    ensure_ui_string_translations,
)


class Command(BaseCommand):
    help = _('Pre-generate LibreTranslate translations for the map popup and UI vocabulary')

    def handle(self, *args, **options):
        institutions = Institution.objects.filter(
            Q(popup_summary__gt='') | Q(popup_content__gt=''),
        )
        for institution in institutions:
            ensure_institution_popup_translations(institution)
            self.stdout.write(f'Translated popup content for "{institution.name}"')

        for ui_string in UIString.objects.all():
            ensure_ui_string_translations(ui_string)
            self.stdout.write(f'Translated UI string "{ui_string.key}"')

        self.stdout.write(self.style.SUCCESS(
            f'Done: {institutions.count()} institution(s), '
            f'{UIString.objects.count()} UI string(s).'
        ))
