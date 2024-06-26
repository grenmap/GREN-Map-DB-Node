# Generated by Django 3.0.2 on 2020-08-14 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StagedNetworkData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(default='2020-08-14T123347', max_length=128)),
                ('file_path', models.FileField(db_index=True, upload_to='not_used')),
                ('name', models.CharField(max_length=128)),
                ('file_date', models.DateTimeField(auto_now_add=True)),
                ('grenml_export_description', models.TextField(default='')),
            ],
        ),
    ]
