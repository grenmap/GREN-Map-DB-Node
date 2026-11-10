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

Synopsis: The map's interface strings follow the English texts and the
hand-written translations in chameleon_api.apps, also on a database
seeded with older texts.
"""
import pytest

from chameleon_api.apps import CURATED_TRANSLATIONS, INITIAL_UI_STRINGS, seed_ui_strings
from chameleon_api.models import UIString, UIStringTranslation


TEXTS = dict(INITIAL_UI_STRINGS)


@pytest.mark.django_db
def test_every_string_is_seeded_with_curated_portuguese():
    seed_ui_strings(None)

    assert dict(UIString.objects.values_list('key', 'text')) == TEXTS
    portuguese = dict(
        UIStringTranslation.objects.filter(language_code='pt')
        .values_list('ui_string__key', 'text')
    )
    assert portuguese == CURATED_TRANSLATIONS['pt']


@pytest.mark.django_db
def test_changed_english_text_replaces_the_old_one_and_its_translations():
    seed_ui_strings(None)
    reminder = UIString.objects.get(key='data_notice_reminder')
    reminder.text = 'Unofficial data · partly AI-extracted'
    reminder.save()
    UIStringTranslation.objects.create(
        ui_string=reminder, language_code='fr', text='Données non officielles',
    )

    seed_ui_strings(None)

    reminder.refresh_from_db()
    assert reminder.text == TEXTS['data_notice_reminder']
    assert not reminder.translations.filter(language_code='fr').exists()
    curated = CURATED_TRANSLATIONS['pt']['data_notice_reminder']
    assert reminder.translations.get(language_code='pt').text == curated


@pytest.mark.django_db
def test_unchanged_strings_keep_their_machine_translations():
    seed_ui_strings(None)
    close = UIString.objects.get(key='close')
    UIStringTranslation.objects.create(ui_string=close, language_code='fr', text='Fermer')

    seed_ui_strings(None)

    assert close.translations.get(language_code='fr').text == 'Fermer'


@pytest.mark.django_db
def test_curated_translation_overwrites_a_machine_one():
    seed_ui_strings(None)
    report = UIString.objects.get(key='report_correction')
    report.translations.filter(language_code='pt').update(text='Relatar uma correcção')

    seed_ui_strings(None)

    assert report.translations.get(language_code='pt').text == 'Sugerir uma correção'
