from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand

from podcasts.models import YouTubePodcast, RSS_FEED_FOLDER_NAME, ARCHIVE_FOLDER_NAME
from podcasts.views.pull_videos import pull_videos


class Command(BaseCommand):
    def handle(self, *args, **options):
        youtube_podcasts = YouTubePodcast.objects.all().filter(url__isnull=False)
        Path(
            f"{settings.MEDIA_ROOT}/{RSS_FEED_FOLDER_NAME}"
        ).mkdir(parents=True, exist_ok=True)
        Path(
            f"{settings.MEDIA_ROOT}/{ARCHIVE_FOLDER_NAME}"
        ).mkdir(parents=True, exist_ok=True)
        for youtube_podcast in youtube_podcasts:
            pull_videos(youtube_podcast)