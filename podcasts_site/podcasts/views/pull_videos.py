import os
import shutil
from pathlib import Path

import yt_dlp

from podcasts.models import YouTubeDLPError
from podcasts.views.Gmail import Gmail
from podcasts.views.delete_videos_that_are_not_properly_processed import delete_videos_that_are_not_properly_processed
from podcasts.views.setup_logger import Loggers
from podcasts.views.youtube_video_post_processor import YouTubeVideoPostProcessor
from podcasts.views.automatically_hide_videos import automatically_hide_videos
from podcasts.views.generate_rss_file import generate_rss_file


def pull_videos(youtube_podcast):
    first_run = False
    youtube_podcast.being_processed = True
    youtube_podcast.save()
    if not youtube_podcast.name:
        youtube_podcast.name = "temp"
        first_run = True
    Path(youtube_podcast.video_file_location).mkdir(parents=True, exist_ok=True)
    with open(youtube_podcast.archive_file_location, 'w') as f:
        for video in youtube_podcast.youtubepodcastvideo_set.all():
            f.write(f"youtube {video.video_id}\n")
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    try:
        def title_filter(info, *, incomplete):
            title = info.get("title")
            substrings = list(
                youtube_podcast.youtubepodcasttitlesubstring_set.all()
                .values_list('title_substring', flat=True)
            )
            prefixes = list(
                youtube_podcast.youtubepodcasttitleprefix_set.all()
                .values_list('title_prefix', flat=True)
            )
            if len(substrings) > 0 or len(prefixes) > 0:
                matches_substring_filter = [
                    1
                    for substring in substrings
                    if substring in title
                ]
                matches_prefix_filter = [
                    1 for prefix in prefixes
                    if title[:len(prefix)] == prefix
                ]
                if len(matches_substring_filter) > 0:
                    pass # keep it
                if len(matches_prefix_filter) > 0:
                    pass # keep it
                else:
                    return f"{title} is not needed"

        # I was previously utilizing the daterange filter, but I switched to playlistend cause when daterange
        # is used, it will check the date of each video in the playlist cause there is no guarantee they are
        # sorted by date and time
        # today = datetime.datetime.now()
        # date_start = (today - datetime.timedelta(days=youtube_podcast.range)).strftime("%Y%m%d")
        # date_end = (today + datetime.timedelta(days=1)).strftime("%Y%m%d")
        yt_opts = {
            'verbose': True,
            # "daterange": DateRange(date_start, date_end),
            "match_filter": title_filter,
            "outtmpl": '%(title)s.%(ext)s',  # done because if not specified, ytdlp adds the video ID to the
            # filename
            "paths": {"home": youtube_podcast.video_file_location},
            "download_archive": youtube_podcast.archive_file_location,  # done so that past downloaded videos
            # are not re-downloaded
            "ignoreerrors": True,  # helpful so that if one video has an issue, the rest will still be
            # attempted to be downloaded
            "sleep_interval_requests": 20,  # to avoid youtube trying to verify the requests are not coming
            # from a bot
            "playlistend": youtube_podcast.index_range,  # stop after the latest 40 videos in a playlist as
            "logger" : youtube_dlp_logger
            # some playlists contain 2000+ videos to sift through
            # "skip_download" : True, # if doing debug
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

    delete_videos_that_are_not_properly_processed(youtube_podcast)
    automatically_hide_videos(youtube_podcast)
    generate_rss_file(youtube_podcast)
    youtube_podcast.being_processed = False
    youtube_podcast.save()
    errors = YouTubeDLPError.objects.all().filter(processed=False)
    if len(errors) > 0:
        gmail = Gmail()
        log_sent = []
        for error in errors:
            if error.error_file_path in log_sent:
                error.processed = True
                error.save()
                continue
            log_sent.append(error.error_file_path)
            gmail.send_email(
                subject="podcast errors", body="look at attachments", to_email=os.environ['TO_EMAIL'], to_name='modernNeo',
                attachments=[error.debug_file_path, error.warn_file_path, error.error_file_path]
            )
            error.processed = True
            error.save()
        gmail.close_connection()
