# Generated by Django 5.1.1 on 2024-09-16 01:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('podcasts', '0002_remove_youtubepodcast_one_process_in_progress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='youtubedlperror',
            name='message',
            field=models.CharField(max_length=10000),
        ),
    ]