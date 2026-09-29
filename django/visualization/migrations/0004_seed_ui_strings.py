from django.db import migrations


INITIAL_UI_STRINGS = [
    ('link_details', 'Link Details'),
    ('connected_to', 'Connected to:'),
    ('managed_by', 'Managed by:'),
    ('close', 'Close'),
]


def seed_ui_strings(apps, schema_editor):
    UIString = apps.get_model('visualization', 'UIString')
    for key, text in INITIAL_UI_STRINGS:
        UIString.objects.get_or_create(key=key, defaults={'text': text})


def unseed_ui_strings(apps, schema_editor):
    UIString = apps.get_model('visualization', 'UIString')
    UIString.objects.filter(
        key__in=[key for key, _text in INITIAL_UI_STRINGS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('visualization', '0003_uistring_uistringtranslation_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_ui_strings, unseed_ui_strings),
    ]
