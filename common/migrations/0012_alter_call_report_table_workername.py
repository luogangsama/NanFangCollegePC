# Generated by Django 5.1.4 on 2024-12-31 03:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0011_alter_call_report_table_workername'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='call_report_table',
            name='workerName',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='call_report_table_profile_worker', to=settings.AUTH_USER_MODEL),
        ),
    ]