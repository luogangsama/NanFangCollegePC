# Generated by Django 5.1.4 on 2024-12-21 15:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_call_report_table_date_call_report_table_issue'),
    ]

    operations = [
        migrations.RenameField(
            model_name='call_report_table',
            old_name='worderName',
            new_name='workerName',
        ),
    ]
