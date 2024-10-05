from pathlib import Path

from django.conf import settings

from podcasts.models import YouTubePodcast, RSS_FEED_FOLDER_NAME, ARCHIVE_FOLDER_NAME, YouTubeDLPError
from podcasts.views.email_errors import email_errors
from podcasts.views.pull_videos import pull_videos


def pull_latest_youtube_videos():
    print("doing a pull")
    YouTubePodcast.objects.all().update(being_processed=False)
    youtube_podcasts = YouTubePodcast.objects.all().filter(url__isnull=False).order_by("id")
    Path(f"{settings.MEDIA_ROOT}/{RSS_FEED_FOLDER_NAME}").mkdir(parents=True, exist_ok=True)
    Path(f"{settings.MEDIA_ROOT}/{ARCHIVE_FOLDER_NAME}").mkdir(parents=True, exist_ok=True)
    YouTubeDLPError.objects.all().delete()
    for youtube_podcast in youtube_podcasts:
        pull_videos(youtube_podcast)
    email_errors()