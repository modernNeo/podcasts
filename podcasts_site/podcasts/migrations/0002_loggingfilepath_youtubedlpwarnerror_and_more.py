# Generated by Django 5.1 on 2024-12-28 02:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoggingFilePath',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error_file_path', models.CharField(default=None, max_length=500, null=True)),
                ('warn_file_path', models.CharField(default=None, max_length=500, null=True)),
                ('debug_file_path', models.CharField(default=None, max_length=500, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='YouTubeDLPWarnError',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error_file_path', models.CharField(default=None, max_length=500, null=True)),
                ('warn_file_path', models.CharField(default=None, max_length=500, null=True)),
                ('debug_file_path', models.CharField(default=None, max_length=500, null=True)),
                ('message', models.CharField(max_length=10000)),
                ('request', models.CharField(default=None, max_length=100000, null=True)),
                ('fixed', models.BooleanField(default=False)),
                ('processed', models.BooleanField(default=False)),
                ('levelno', models.IntegerField(default=30)),
                ('video_unavailable', models.BooleanField(null=True)),
                ('podcast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='podcasts.youtubepodcast')),
            ],
        ),
        migrations.DeleteModel(
            name='YouTubeDLPError',
        ),
    ]
