from podcasts.models import YouTubePodcast
from podcasts.views.setup_logger import Loggers


def update_archive_file(youtube_podcast: YouTubePodcast):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    with open(youtube_podcast.archive_file_location, 'w') as f:
        for video in youtube_podcast.youtubevideo_set.all():
            if video.is_present():
                video.file_not_found = False
                f.write(f"youtube {video.video_id}\n")
            else:
                video.file_not_found = True
                youtube_dlp_logger.warn(
                    f"[update_archive_file]\n\t[{video}] not in \n\t\t{youtube_podcast.video_file_location}"
                )
                # video.delete()
            video.save()
