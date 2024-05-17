# Generated by Django 3.2.13 on 2022-08-10 18:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RSIdentity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eppn', models.CharField(error_messages={'unique': 'A R&S Identity with that eppn already exists.'}, max_length=150, unique=True, verbose_name='eduPerson Principal Name')),
                ('email', models.EmailField(blank=True, default='', max_length=254, verbose_name='email')),
                ('display_name', models.CharField(blank=True, default='', max_length=150, verbose_name='Display Name')),
                ('first_name', models.CharField(blank=True, default='', max_length=150, verbose_name='First Name')),
                ('last_name', models.CharField(blank=True, default='', max_length=150, verbose_name='Last Name')),
                ('user', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'RS Identity',
                'verbose_name_plural': 'RS Identities',
            },
        ),
    ]
