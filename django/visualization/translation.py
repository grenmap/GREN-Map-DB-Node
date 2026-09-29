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

Synopsis: Calls LibreTranslate to translate institution popup content
and fixed map interface vocabulary, caching the results.
"""

import logging

import requests
from django.conf import settings

from .models import InstitutionPopupTranslation, UIStringTranslation


log = logging.getLogger('visualization')


def translate(text, target, source='en', fmt='text'):
    """
    Calls the LibreTranslate service to translate 'text' from 'source'
    to 'target'. Returns the translated string, or None if the service
    is unavailable or errors out. Never raises: callers are expected
    to fall back gracefully (e.g. skip the translation) rather than
    fail the map API when the translator is down.
    """
    if not text:
        return ''

    try:
        response = requests.post(
            settings.LIBRETRANSLATE_URL,
            json={
                'q': text,
                'source': source,
                'target': target,
                'format': fmt,
            },
            timeout=settings.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()['translatedText']
    except Exception:
        log.exception(f'LibreTranslate request failed translating to "{target}"')
        return None


def ensure_institution_popup_translations(institution, source='en'):
    """
    Makes sure a translation exists, for every configured language
    other than the source language, of the given Institution's
    popup_summary/popup_content. Missing translations are generated
    via LibreTranslate and cached. Returns the list of
    InstitutionPopupTranslation rows for this institution.
    """
    translations = []

    for language_code, _label in settings.LANGUAGES:
        if language_code == source:
            continue

        translation, created = InstitutionPopupTranslation.objects.get_or_create(
            institution=institution,
            language_code=language_code,
        )

        if created or (not translation.summary and not translation.full_content):
            summary = translate(institution.popup_summary, language_code, source, fmt='text')
            full_content = translate(institution.popup_content, language_code, source, fmt='html')

            if summary is not None:
                translation.summary = summary
            if full_content is not None:
                translation.full_content = full_content
            translation.save()

        translations.append(translation)

    return translations


def ensure_ui_string_translations(ui_string, source='en'):
    """
    Makes sure a translation exists, for every configured language
    other than the source language, of the given UIString's text.
    Missing translations are generated via LibreTranslate and cached.
    Returns the list of UIStringTranslation rows for this string.
    """
    translations = []

    for language_code, _label in settings.LANGUAGES:
        if language_code == source:
            continue

        translation, created = UIStringTranslation.objects.get_or_create(
            ui_string=ui_string,
            language_code=language_code,
        )

        if created or not translation.text:
            text = translate(ui_string.text, language_code, source, fmt='text')
            if text is not None:
                translation.text = text
                translation.save()

        translations.append(translation)

    return translations
