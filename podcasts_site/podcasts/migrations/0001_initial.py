# Generated by Django 5.1 on 2024-10-11 02:42

import django.db.models.deletion
import podcasts.views.pstdatetimefield
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CronSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hour', models.IntegerField()),
                ('minute', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='YouTubeDLPError',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error_file_path', models.CharField(default=None, max_length=500, null=True)),
                ('warn_file_path', models.CharField(default=None, max_length=500, null=True)),
                ('debug_file_path', models.CharField(default=None, max_length=500, null=True)),
                ('message', models.CharField(max_length=10000)),
                ('request', models.CharField(default=None, max_length=100000, null=True)),
                ('fixed', models.BooleanField(default=False)),
                ('processed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='YouTubePodcast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1000)),
                ('custom_name', models.CharField(max_length=1000, null=True)),
                ('description', models.CharField(max_length=5000)),
                ('image', models.CharField(max_length=10000, null=True)),
                ('language', models.CharField(max_length=5)),
                ('author', models.CharField(max_length=10000)),
                ('url', models.CharField(max_length=10000)),
                ('when_to_pull', models.TimeField()),
                ('being_processed', models.BooleanField(default=False)),
                ('category', models.CharField(max_length=1000)),
                ('index_range', models.IntegerField(null=True)),
                ('information_last_updated', podcasts.views.pstdatetimefield.PSTDateTimeField(null=True)),
                ('cbc_news', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='YouTubeVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_id', models.CharField(max_length=1000, unique=True)),
                ('filename', models.CharField(max_length=1000)),
                ('original_title', models.CharField(max_length=1000)),
                ('description', models.CharField(max_length=5000)),
                ('date', podcasts.views.pstdatetimefield.PSTDateTimeField()),
                ('identifier_number', models.PositiveBigIntegerField()),
                ('grouping_number', models.IntegerField()),
                ('url', models.CharField(max_length=10000, unique=True)),
                ('extension', models.CharField(max_length=100)),
                ('image', models.CharField(max_length=10000, null=True)),
                ('size', models.PositiveBigIntegerField()),
                ('hide', models.BooleanField(default=False)),
                ('manually_hide', models.BooleanField(default=False)),
                ('duration', models.PositiveBigIntegerField()),
                ('file_not_found', models.BooleanField(default=False)),
                ('podcast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='podcasts.youtubepodcast')),
            ],
        ),
        migrations.CreateModel(
            name='PodcastVideoGrouping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grouping_number', models.IntegerField()),
                ('podcast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='podcasts.youtubepodcast')),
                ('podcast_video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='podcasts.youtubevideo')),
            ],
        ),
        migrations.CreateModel(
            name='YouTubePodcastTitlePrefix',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_prefix', models.CharField(default=None, max_length=1000, null=True)),
                ('priority', models.IntegerField(default=None)),
                ('podcast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='podcasts.youtubepodcast')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('podcast', 'priority'), name='unique_podcast_title_prefix_priority')],
            },
        ),
        migrations.CreateModel(
            name='YouTubePodcastTitleSubString',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_substring', models.CharField(default=None, max_length=1000, null=True)),
                ('priority', models.IntegerField(default=None)),
                ('podcast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='podcasts.youtubepodcast')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('podcast', 'priority'), name='unique_podcast_title_substring_priority')],
            },
        ),
    ]
