# Generated by Django 3.2.19 on 2023-05-18 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('published_network_data', '0005_auto_20220907_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publishednetworkdata',
            name='published_status',
            field=models.CharField(default='pending', max_length=128),
        ),
    ]