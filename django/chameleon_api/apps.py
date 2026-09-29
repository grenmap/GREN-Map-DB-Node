from django.apps import AppConfig
from django.db.models.signals import post_migrate


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
    # Popup modal footer. The prompt is followed by the institution
    # name and a "?" -- names are never sent to machine translation.
    ('report_correction_prompt', 'Something wrong or outdated in the information about'),
    ('report_correction', 'Report a correction'),
    ('report_correction_hint', 'Opens your email app with the node and institution pre-filled'),
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


class ChameleonApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chameleon_api'

    def ready(self):
        super().ready()
        post_migrate.connect(seed_ui_strings, sender=self)
