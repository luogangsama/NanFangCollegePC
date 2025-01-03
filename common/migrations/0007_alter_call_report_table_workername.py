# Generated by Django 5.1.4 on 2024-12-23 19:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_alter_call_report_table_user_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='call_report_table',
            name='workerName',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='call_report_table_profile_worker', to=settings.AUTH_USER_MODEL),
        ),
    ]
