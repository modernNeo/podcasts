import os
import shutil
import sys
from pathlib import Path

import yt_dlp
from yt_dlp.networking.exceptions import HTTPError
from yt_dlp.utils import ExtractorError

from podcasts.models import YouTubeDLPWarnError, YouTubePodcast
from podcasts.views.automatically_hide_videos import automatically_hide_videos
from podcasts.views.delete_videos_that_are_not_properly_tracked import delete_videos_that_are_not_properly_tracked
from podcasts.views.generate_rss_file import generate_rss_file
from podcasts.views.match_filter import match_filter
from podcasts.views.setup_logger import Loggers, error_logging_level, warn_logging_level
from podcasts.views.update_archive_file import update_archive_file
from podcasts.views.youtube_video_post_processor import YouTubeVideoPostProcessor


def get_youtube_id(message):
    youtube_tag = " [youtube]"
    if youtube_tag not in message:
        return None
    youtube_tag_index = message.index(youtube_tag)
    tag_part_of_message = message[youtube_tag_index + len(youtube_tag)+1:]
    end_index_of_tag = tag_part_of_message.index(":")
    return tag_part_of_message[:end_index_of_tag]

class CustomDL(yt_dlp.YoutubeDL):

    def report_warning(self, message, only_once=False):
        """
        Print the message to stderr, it will be prefixed with 'WARNING:'
        If stderr is a tty file the 'WARNING:' will be colored
        """
        if self.params.get('logger') is not None:
            common_data_retrieval_log_messages = (
                    '[youtube:tab] Incomplete data received. Retrying' in message or
                    '[youtube:tab] Incomplete data received. Giving up after 3 retries' in message
            )
            podcast_being_processed = YouTubePodcast.objects.all().filter(being_processed=True).first()
            podcasts_with_known_retrieval_issues = (
                'The Weekly Show with Jon Stewart | FULL Episodes'
            )
            podcasts_known_to_be_problematic = (
                    podcast_being_processed is not None and
                    podcast_being_processed.name in podcasts_with_known_retrieval_issues
            )
            if common_data_retrieval_log_messages and podcasts_known_to_be_problematic:
                # https://github.com/yt-dlp/yt-dlp/issues/11930#issuecomment-2564490472
                self.params['logger'].info(message)
                return
            elif not podcasts_known_to_be_problematic:
                self.params['logger'].warning(f"[{podcast_being_processed.name}]")
        super().report_warning(message, only_once=only_once)

    def trouble(self, message=None, tb=None, is_error=True):
        video_unavailable = False
        podcast_being_processed = None
        log_level = error_logging_level

        if sys.exc_info()[0]:
            exception = sys.exc_info()[1]
            if type(exception) is ExtractorError:
                private_video = (
                        "Private video. Sign in if you've been granted access to this video"
                        in exception.msg or
                        "Video unavailable. This video is private" in exception.msg
                )
                removed_video = (
                        "Video unavailable. This video has been removed by the uploader" in exception.msg
                )
                if private_video or removed_video:
                    self.params['logger'].debug(message)
                    return
                elif "Video unavailable" in exception.msg:
                    self.params['logger'].warn(message)
                    log_level = warn_logging_level
                    video_unavailable = True
            else:
                podcast_being_processed = YouTubePodcast.objects.all().filter(being_processed=True).first()
                self.params['logger'].error(f'{message} for {podcast_being_processed}')
                video_unavailable = True

        if podcast_being_processed is None:
            podcast_being_processed = YouTubePodcast.objects.all().filter(being_processed=True).first()
        YouTubeDLPWarnError(
            message=message, levelno=log_level, video_unavailable=video_unavailable,
            podcast=podcast_being_processed, video_id=get_youtube_id(message)
        ).save()
        if video_unavailable:
            return
        super().trouble(message=message, tb=tb, is_error=is_error)


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
            "paths": {"home": f"{youtube_podcast.video_file_location}"},
            "download_archive": youtube_podcast.archive_file_location,  # done so that past downloaded videos
            # are not re-downloaded
            "sleep_interval_requests": 20,  # to avoid youtube trying to verify the requests are not coming from a bot
            "playlistend": youtube_podcast.index_range,
            "logger" : Loggers.get_logger("youtube_dlp"),
            "ffmpeg_location" : "ffmpeg-master-latest-linux64-gpl/bin/ffmpeg",
            "format_sort": ['vcodec:avc', 'res', 'acodec:aac'], # needed cause of
            # https://github.com/yt-dlp/yt-dlp/issues/11177#issuecomment-2395588715
            "extractor_args": {"youtube": {"player_client": ["default", "-tv_simply"]}}, # fixing latest yt-dlp bug
            # with arg from https://github.com/yt-dlp/yt-dlp/issues/14456#issuecomment-3339654496
            "cookiefile" : os.environ.get('COOKIE_LOCATION', None),
            'format': 'bv+ba/b' # needed cause of https://github.com/yt-dlp/yt-dlp/issues/14462#issuecomment-3340774234

            # useful for debugging
            # "listformats" : True
            # "skip_download" : True
        }

        with CustomDL(yt_opts) as ydl:
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

