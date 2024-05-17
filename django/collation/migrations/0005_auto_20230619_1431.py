# Generated by Django 3.2.19 on 2023-06-19 14:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('collation', '0004_default_id_collision_rulesets'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='action_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='collation.actiontype', verbose_name='action type'),
        ),
        migrations.AlterField(
            model_name='action',
            name='rule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='collation.rule', verbose_name='rule'),
        ),
        migrations.AlterField(
            model_name='actioninfo',
            name='action',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='collation.action', verbose_name='action'),
        ),
        migrations.AlterField(
            model_name='actioninfo',
            name='key',
            field=models.CharField(max_length=50, verbose_name='key'),
        ),
        migrations.AlterField(
            model_name='actioninfo',
            name='value',
            field=models.CharField(max_length=1000, verbose_name='value'),
        ),
        migrations.AlterField(
            model_name='actiontype',
            name='class_name',
            field=models.CharField(max_length=200, unique=True, verbose_name='class name'),
        ),
        migrations.AlterField(
            model_name='actiontype',
            name='element_type',
            field=models.CharField(choices=[('Institution', 'Institution'), ('Node', 'Node'), ('Link', 'Link')], max_length=20, verbose_name='element type'),
        ),
        migrations.AlterField(
            model_name='actiontype',
            name='name',
            field=models.CharField(max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='actiontype',
            name='optional_info',
            field=models.CharField(blank=True, default='', help_text='JSON array of optional ActionInfo keys', max_length=200, null=True, verbose_name='optional info'),
        ),
        migrations.AlterField(
            model_name='actiontype',
            name='required_info',
            field=models.CharField(blank=True, help_text='JSON array of required ActionInfo keys', max_length=200, null=True, verbose_name='required info'),
        ),
        migrations.AlterField(
            model_name='matchcriterion',
            name='match_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='collation.matchtype', verbose_name='match type'),
        ),
        migrations.AlterField(
            model_name='matchcriterion',
            name='rule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='match_criteria', to='collation.rule', verbose_name='rule'),
        ),
        migrations.AlterField(
            model_name='matchinfo',
            name='key',
            field=models.CharField(max_length=50, verbose_name='key'),
        ),
        migrations.AlterField(
            model_name='matchinfo',
            name='match_criterion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='collation.matchcriterion', verbose_name='match criterion'),
        ),
        migrations.AlterField(
            model_name='matchinfo',
            name='value',
            field=models.CharField(max_length=1000, verbose_name='value'),
        ),
        migrations.AlterField(
            model_name='matchtype',
            name='class_name',
            field=models.CharField(max_length=200, unique=True, verbose_name='class name'),
        ),
        migrations.AlterField(
            model_name='matchtype',
            name='element_type',
            field=models.CharField(choices=[('Institution', 'Institution'), ('Node', 'Node'), ('Link', 'Link')], max_length=20, verbose_name='element type'),
        ),
        migrations.AlterField(
            model_name='matchtype',
            name='name',
            field=models.CharField(max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='matchtype',
            name='optional_info',
            field=models.CharField(blank=True, default='', help_text='JSON array of optional ActionInfo keys', max_length=200, null=True, verbose_name='optional info'),
        ),
        migrations.AlterField(
            model_name='matchtype',
            name='required_info',
            field=models.CharField(blank=True, help_text='JSON array of required ActionInfo keys', max_length=200, null=True, verbose_name='required info'),
        ),
        migrations.AlterField(
            model_name='rule',
            name='enabled',
            field=models.BooleanField(default=True, verbose_name='enabled'),
        ),
        migrations.AlterField(
            model_name='rule',
            name='name',
            field=models.CharField(max_length=200, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='rule',
            name='priority',
            field=models.SmallIntegerField(default=1000, help_text='Rules within a Ruleset are run in ascending order of priority. Ties are broken arbitrarily.', verbose_name='priority'),
        ),
        migrations.AlterField(
            model_name='rule',
            name='ruleset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='collation.ruleset', verbose_name='ruleset'),
        ),
        migrations.AlterField(
            model_name='ruleset',
            name='enabled',
            field=models.BooleanField(default=True, verbose_name='enabled'),
        ),
        migrations.AlterField(
            model_name='ruleset',
            name='name',
            field=models.CharField(max_length=200, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='ruleset',
            name='priority',
            field=models.SmallIntegerField(default=1000, help_text='Rulesets are run in ascending order of priority. Ties are broken arbitrarily.', verbose_name='priority'),
        ),
    ]