# Generated by Django 3.2.13 on 2022-08-15 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base_app', '0004_alter_token_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='token',
            name='token_associated_app',
        ),
        migrations.AddField(
            model_name='token',
            name='token_type',
            field=models.CharField(blank=True, choices=[('grenml_import', 'Import'), ('grenml_export', 'Polling')], default='grenml_export', max_length=255, null=True),
        ),
    ]
