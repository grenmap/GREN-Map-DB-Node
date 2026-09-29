from django.core.management.base import BaseCommand
from django.db.models import Q

from network_topology.models import Institution
from chameleon_api.models import UIString
from chameleon_api.translation import (
    ensure_institution_popup_translations,
    ensure_ui_string_translations,
)


class Command(BaseCommand):
    help = (
        'Pre-generates and caches LibreTranslate translations for all '
        'Institution popup content and UIString map vocabulary, so the '
        'first chameleon_api request for each does not have to wait on '
        'the translator.'
    )

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
