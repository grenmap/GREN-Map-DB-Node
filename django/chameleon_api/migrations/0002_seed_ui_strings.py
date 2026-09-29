from django.db import migrations


INITIAL_UI_STRINGS = [
    ('link_details', 'Link Details'),
    ('connected_to', 'Connected to:'),
    ('managed_by', 'Managed by:'),
    ('close', 'Close'),
]


def seed_ui_strings(apps, schema_editor):
    UIString = apps.get_model('chameleon_api', 'UIString')
    for key, text in INITIAL_UI_STRINGS:
        UIString.objects.get_or_create(key=key, defaults={'text': text})


def unseed_ui_strings(apps, schema_editor):
    UIString = apps.get_model('chameleon_api', 'UIString')
    UIString.objects.filter(
        key__in=[key for key, _text in INITIAL_UI_STRINGS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('chameleon_api', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_ui_strings, unseed_ui_strings),
    ]
