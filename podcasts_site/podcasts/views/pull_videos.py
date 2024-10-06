import os
import shutil
from pathlib import Path

import yt_dlp

from podcasts.views.automatically_hide_videos import automatically_hide_videos
from podcasts.views.delete_videos_that_are_not_properly_tracked import delete_videos_that_are_not_properly_tracked
from podcasts.views.generate_rss_file import generate_rss_file
from podcasts.views.match_filter import match_filter
from podcasts.views.setup_logger import Loggers
from podcasts.views.update_archive_file import update_archive_file
from podcasts.views.youtube_video_post_processor import YouTubeVideoPostProcessor


def pull_videos(youtube_podcast):
    first_run = False
    youtube_podcast.being_processed = True
    youtube_podcast.save()
    if not youtube_podcast.name:
        youtube_podcast.name = "temp"
        first_run = True
    Path(youtube_podcast.video_file_location).mkdir(parents=True, exist_ok=True)
    delete_videos_that_are_not_properly_tracked(youtube_podcast)
    automatically_hide_videos(youtube_podcast)
    update_archive_file(youtube_podcast)
    generate_rss_file(youtube_podcast)
    try:
        yt_opts = {
            'verbose': True,
            "match_filter": match_filter,
            "outtmpl": '%(title)s.%(ext)s',  # done because if not specified, ytdlp adds the video ID to the filename
            "paths": {"home": youtube_podcast.video_file_location},
            "download_archive": youtube_podcast.archive_file_location,  # done so that past downloaded videos
            # are not re-downloaded
            "ignoreerrors": True,  # helpful so that if one video has an issue, the rest will still be
            # attempted to be downloaded
            "sleep_interval_requests": 20,  # to avoid youtube trying to verify the requests are not coming
            # from a bot
            "playlistend": youtube_podcast.index_range,
            "logger" : Loggers.get_logger("youtube_dlp"),
            "ffmpeg_location" : "ffmpeg-N-117339-gf25c9cc213-linux64-gpl/bin/ffmpeg",
            "format":  "bv*[ext=mp4]+ba[ext=m4a]",
            "format_sort" : ["vcodec:h264"]

            # useful for debugging
            # "listformats" : True
            # "skip_download" : True
        }
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            ydl.add_post_processor(YouTubeVideoPostProcessor())
            ydl.download(youtube_podcast.url)
    except (yt_dlp.utils.ExistingVideoReached, yt_dlp.utils.DownloadError):
        pass
    previous_video_file_location = youtube_podcast.video_file_location
    previous_archive_file_location = youtube_podcast.archive_file_location
    youtube_podcast.refresh_from_db()
    if first_run:
        if os.path.exists(youtube_podcast.video_file_location):
            shutil.rmtree(youtube_podcast.video_file_location)
        os.rename(previous_video_file_location, youtube_podcast.video_file_location)
        os.rename(previous_archive_file_location, youtube_podcast.archive_file_location)

    delete_videos_that_are_not_properly_tracked(youtube_podcast)
    automatically_hide_videos(youtube_podcast)
    update_archive_file(youtube_podcast)
    generate_rss_file(youtube_podcast)
    youtube_podcast.being_processed = False
    youtube_podcast.save()

