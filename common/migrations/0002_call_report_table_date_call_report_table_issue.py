# Generated by Django 5.1.4 on 2024-12-21 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='call_report_table',
            name='date',
            field=models.CharField(default=0, max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='call_report_table',
            name='issue',
            field=models.CharField(default=0, max_length=200),
            preserve_default=False,
        ),
    ]
