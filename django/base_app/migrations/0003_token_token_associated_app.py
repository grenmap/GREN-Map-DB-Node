# Generated by Django 3.0.14 on 2022-03-10 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base_app', '0002_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='token_associated_app',
            field=models.CharField(blank=True, choices=[('grenml_import', 'Import Token For External Use'), ('grenml_export', 'Collecting Token For External Use')], default='grenml_export', help_text='This identifies the APP which will be using this token.', max_length=255, null=True),
        ),
    ]
