# Generated by Django 3.2.16 on 2022-11-16 15:25

from django.db import migrations, models
import network_topology.models.base_model


class Migration(migrations.Migration):

    dependencies = [
        ('network_topology', '0001_squashed_0010_alter_basemodel_pk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basemodel',
            name='grenml_id',
            field=models.CharField(blank=True, default=network_topology.models.base_model.auto_uuid, help_text='Supply a unique ID for this item.<br />Minimum: UUID or hash.<br />Good: ID consistent with your REN records, (beware publishing sensitive data).<br />Best: namespace-prefix the above somehow to avoid collisions.<br />Example: "myren-sunlighttransatlantic47"<br />Ideally co-ordinate with other RENs for common IDs of shared infrastructure.<br />If omitted, an ID will be auto-generated for this object.', max_length=128, verbose_name='GRENML ID'),
        ),
    ]
