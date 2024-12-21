# Generated by Django 5.1.4 on 2024-12-21 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='call_report_table',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=200)),
                ('userPhoneNumber', models.CharField(max_length=11)),
                ('address', models.CharField(max_length=50)),
                ('allocationState', models.BooleanField(default=False)),
                ('completeState', models.BooleanField(default=False)),
                ('workerPhoneNumber', models.CharField(max_length=11)),
                ('worderName', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=200)),
                ('password', models.CharField(max_length=256)),
                ('label', models.CharField(max_length=2)),
            ],
        ),
    ]
