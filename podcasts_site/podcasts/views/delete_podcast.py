import os
import shutil

from django.conf import settings

from podcasts.models import YouTubePodcast, VIDEOS_FOLDER_NAME, ARCHIVE_FOLDER_NAME


def delete_podcast(podcast_id):
    podcast = YouTubePodcast.objects.all().filter(id=int(podcast_id)).first()
    if podcast:
        podcast.being_processed = False
        for video in podcast.youtubevideo_set.all():
            video.delete()
        podcast.save()

        if podcast.files_to_delete_available:
            try:
                shutil.rmtree(podcast.video_file_location)
            except FileNotFoundError:
                pass
            try:
                os.remove(podcast.archive_file_location)
            except (FileNotFoundError, IsADirectoryError):
                pass
            try:
                os.remove(podcast.feed_file_location)
            except FileNotFoundError:
                pass
        podcast.delete()