import os

from podcasts.models import YouTubePodcast
from podcasts.views.setup_logger import Loggers


def delete_videos_that_are_not_properly_tracked(youtube_podcast: YouTubePodcast):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    ## deleting any videos in the file system that aren't tracked in the D.B.
    tracked_videos = youtube_podcast.get_video_filenames()
    # youtube_dlp_logger.info(f"total list of videos for [{youtube_podcast}]: {tracked_videos}")
    for video in os.listdir(youtube_podcast.video_file_location):
        if video not in tracked_videos:
            video_full_path = f"{youtube_podcast.video_file_location}/{video}"
            youtube_dlp_logger.warn(
                f"[delete_videos_that_are_not_properly_tracked]\n\t[{video_full_path}] not in\n\t\t"
                f"{youtube_podcast.video_file_location}"
            )
            # os.remove(video_full_path)