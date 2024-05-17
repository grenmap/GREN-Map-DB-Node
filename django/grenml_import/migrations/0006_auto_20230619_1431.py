# Generated by Django 3.2.19 on 2023-06-19 14:31

from django.db import migrations, models
import django.db.models.deletion
import grenml_import.models


class Migration(migrations.Migration):

    dependencies = [
        ('network_topology', '0005_auto_20230619_1431'),
        ('grenml_import', '0005_auto_20230322_1612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='importdata',
            name='grenml_data',
            field=models.TextField(default='', verbose_name='GRENML data'),
        ),
        migrations.AlterField(
            model_name='importdata',
            name='import_message',
            field=models.TextField(default='', verbose_name='import message'),
        ),
        migrations.AlterField(
            model_name='importdata',
            name='import_status',
            field=models.CharField(default='0: Import in progress', max_length=100, verbose_name='import status'),
        ),
        migrations.AlterField(
            model_name='importdata',
            name='imported_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Imported at'),
        ),
        migrations.AlterField(
            model_name='importdata',
            name='parent_topology',
            field=models.ForeignKey(blank=True, default=None, help_text="The imported file's root Topology will be added as a child of the selected Topology. To add a file's contents as a top-level Topology, select the blank entry here.", null=True, on_delete=django.db.models.deletion.SET_NULL, to='network_topology.topology', verbose_name='Parent topology'),
        ),
        migrations.AlterField(
            model_name='importdata',
            name='source',
            field=models.CharField(max_length=255, verbose_name='Source'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='file',
            field=models.FileField(upload_to=grenml_import.models.file_name, verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='import_message',
            field=models.TextField(default='', verbose_name='import message'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='import_status',
            field=models.CharField(default='0: Import in progress', max_length=100, verbose_name='import status'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='imported_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Imported at'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='name',
            field=models.CharField(max_length=64, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='parent_topology',
            field=models.ForeignKey(blank=True, default=None, help_text="The imported file's root Topology will be added as a child of the selected Topology. To add a file's contents as a top-level Topology, select the blank entry here.", null=True, on_delete=django.db.models.deletion.SET_NULL, to='network_topology.topology', verbose_name='Parent topology'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='source',
            field=models.CharField(choices=[('adm', 'admin import'), ('api', 'API import')], default='adm', help_text='We can import files using the admin interface or the API endpoint.', max_length=3, verbose_name='Source'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='token_client_name',
            field=models.CharField(help_text='Equal to the client name associated to the access token in the import request. Imports done through the admin interface will use the null value.', max_length=255, null=True, verbose_name='Token client name'),
        ),
        migrations.AlterField(
            model_name='importfile',
            name='topology_name',
            field=models.CharField(blank=True, help_text='New name for the imported topology. Required for Excel .xlsx files. Not applicable for .grenml or .xml files. ', max_length=128, null=True, verbose_name='Topology name'),
        ),
    ]
