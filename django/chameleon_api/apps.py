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
    ('report_correction_hint', 'Opens your email app with the institution pre-filled'),
    # Notice on the first visit that the data is unofficial and partly
    # AI-extracted, and the reminder that reopens it.
    ('data_notice_title', 'About the data on this map'),
    ('data_notice_body', (
        'REN Map is a community project, not an official source. The network '
        'topologies were compiled semi-automatically and partly extracted with AI, '
        'so some information may be wrong or out of date.'
    )),
    ('data_notice_levels', (
        'Every network shows its level and when its topology was last updated. '
        'Spotted a mistake? Use "Report a correction" in any network, or propose '
        'a fix on GitHub.'
    )),
    ('data_notice_learn_more', 'How the data is maintained'),
    ('data_notice_dismiss', 'Got it'),
    ('data_notice_reminder', 'Unofficial data · partly AI-extracted'),
    ('data_notice_reminder_hint', (
        'Topologies were compiled semi-automatically and partly with AI. '
        'Click to read the full notice.'
    )),
    # Per-network trust badge. "Verified by" is followed by who verified
    # it and the date -- neither goes through machine translation.
    ('trust_ai_generated', 'AI-generated'),
    ('trust_ai_generated_hint', 'extracted automatically, not yet checked'),
    ('trust_ai_generated_tooltip', (
        "This data was extracted automatically and hasn't been reviewed by a person yet."
    )),
    ('trust_verified', 'Verified'),
    ('trust_verified_hint', 'reviewed by a member of the community'),
    ('verified_by', 'Verified by'),
    # When the network's topology last changed; followed by the date.
    ('updated_on', 'Updated'),
    ('topology_updated_on', 'Topology updated'),
    ('view_latest_change', 'View latest change'),
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
