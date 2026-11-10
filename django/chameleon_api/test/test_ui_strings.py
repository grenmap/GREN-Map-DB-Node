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
    # "close" has no hand-written translation in any language, so every
    # translation left on it would be a stale machine one.
    assert not any('close' in texts for texts in CURATED_TRANSLATIONS.values())
    seed_ui_strings(None)
    label = UIString.objects.get(key='close')
    label.text = 'Close it (old text)'
    label.save()
    UIStringTranslation.objects.create(ui_string=label, language_code='fr', text='Fermez-le')

    seed_ui_strings(None)

    label.refresh_from_db()
    assert label.text == TEXTS['close']
    assert not label.translations.exists()


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


@pytest.mark.django_db
def test_curated_translations_fit_the_column():
    limit = UIStringTranslation._meta.get_field('text').max_length
    for texts in CURATED_TRANSLATIONS.values():
        for key, text in texts.items():
            assert len(text) <= limit, key


@pytest.mark.django_db
def test_too_long_machine_translation_is_skipped_not_an_error(monkeypatch):
    from chameleon_api import translation

    seed_ui_strings(None)
    close = UIString.objects.get(key='close')
    monkeypatch.setattr(translation, 'translate', lambda *args, **kwargs: 'x' * 300)

    rows = translation.ensure_ui_string_translations(close)

    assert rows and all(row.text == '' for row in rows if row.language_code == 'fr')
