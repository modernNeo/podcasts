import os
import shutil

from django.conf import settings

from podcasts.models import YouTubePodcast, VIDEOS_FOLDER_NAME, ARCHIVE_FOLDER_NAME


def reset_podcast(podcast_id):
    podcast = YouTubePodcast.objects.all().filter(id=int(podcast_id)).first()
    if podcast:
        podcast.being_processed = False
        for video in podcast.youtubepodcastvideo_set.all():
            video.delete()
        for video in podcast.duplicateyoutubepodcastvideo_set.all():
            video.delete()
        podcast.save()
        try:
            shutil.rmtree(podcast.video_file_location)
        except FileNotFoundError:
            pass
        try:
            shutil.rmtree(f"{settings.MEDIA_ROOT}/{VIDEOS_FOLDER_NAME}/temp")
        except FileNotFoundError:
            pass
        try:
            os.remove(podcast.archive_file_location)
        except (FileNotFoundError, IsADirectoryError):
            pass
        try:
            os.remove(f"{settings.MEDIA_ROOT}/{ARCHIVE_FOLDER_NAME}/temp")
        except FileNotFoundError:
            pass
        try:
            os.remove(podcast.feed_file_location)
        except FileNotFoundError:
            pass