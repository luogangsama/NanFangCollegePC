# Generated by Django 5.1.4 on 2024-12-30 06:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0009_remove_call_report_table_allocationstate_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='dutyTime',
            field=models.CharField(default='0', max_length=1),
        ),
        migrations.AlterField(
            model_name='call_report_table',
            name='call_date',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='call_report_table',
            name='date',
            field=models.CharField(max_length=50),
        ),
    ]
