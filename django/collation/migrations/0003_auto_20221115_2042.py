# Generated by Django 3.2.16 on 2022-11-15 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collation', '0002_auto_20220510_1844'),
    ]

    operations = [
        migrations.AddField(
            model_name='rule',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='rule',
            name='priority',
            field=models.SmallIntegerField(default=1000, help_text='Rules within a Ruleset are run in ascending order of priority. Ties are broken arbitrarily.'),
        ),
        migrations.AddField(
            model_name='ruleset',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='ruleset',
            name='priority',
            field=models.SmallIntegerField(default=1000, help_text='Rulesets are run in ascending order of priority. Ties are broken arbitrarily.'),
        ),
        migrations.AddField(
            model_name='matchtype',
            name='optional_info',
            field=models.CharField(blank=True, default='', help_text='JSON array of optional ActionInfo keys', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='actiontype',
            name='optional_info',
            field=models.CharField(blank=True, default='', help_text='JSON array of optional ActionInfo keys', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='actiontype',
            name='required_info',
            field=models.CharField(blank=True, help_text='JSON array of required ActionInfo keys', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='matchtype',
            name='required_info',
            field=models.CharField(blank=True, help_text='JSON array of required ActionInfo keys', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='action',
            name='rule',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='actions', to='collation.rule'),
        ),
        migrations.AlterField(
            model_name='matchcriterion',
            name='rule',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='match_criteria', to='collation.rule'),
        ),
        migrations.AlterField(
            model_name='rule',
            name='ruleset',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='rules', to='collation.ruleset'),
        ),
    ]