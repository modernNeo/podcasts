import os
import re
import shutil
import sys
from pathlib import Path

import yt_dlp
from django.conf import settings
from yt_dlp.utils import ExtractorError, DownloadCancelled

from podcasts.models import YouTubePodcast, ARCHIVE_FOLDER_PATH, TroubleRecord
from podcasts.views.automatically_hide_videos import automatically_hide_videos
from podcasts.views.delete_videos_that_are_not_properly_tracked import delete_videos_that_are_not_properly_tracked
from podcasts.views.generate_rss_file import generate_rss_file
from podcasts.views.match_filter import match_filter
from podcasts.views.setup_logger import Loggers, error_logging_level, warn_logging_level
from podcasts.views.update_archive_file import update_archive_file
from podcasts.views.youtube_video_post_processor import YouTubeVideoPostProcessor

MESSAGES_TO_SKIP_PAST_AND_NOT_LOG = [
'[youtube] Video unavailable. This video has been removed by the uploader'
    # 'Unable to download format 95. Skipping...',
    # 'ERROR: \r[download] Got error: HTTP Error 403: Forbidden'
]

REMOVED_BY_UPLOADER = []

class CustomDL(yt_dlp.YoutubeDL):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamic tracking state
        self._currently_parsing_url = None

    def extract_info(self, url, *args, **kwargs):
        """Intercepts when an extraction begins to track the active URL."""
        self._currently_parsing_url = url
        try:
            return super().extract_info(url, *args, **kwargs)
        finally:
            # Clean up after extraction is complete (optional, but good practice)
            self._currently_parsing_url = None

    def download(self, url_list, *args, **kwargs):
        """Intercepts when a list of downloads begins."""
        if url_list and isinstance(url_list, list):
            self._currently_parsing_url = url_list[0]
        try:
            return super().download(url_list, *args, **kwargs)
        finally:
            self._currently_parsing_url = None

    def _get_active_video_id(self):
        """Attempts to look at the intercepted URL first, then falls back to regex."""
        # 1. Use our custom intercepted URL if it's set
        if self._currently_parsing_url:
            # Simple regex helper to grab an 11-char ID from a Youtube link if possible
            match = re.search(r'(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})',
                              self._currently_parsing_url)
            if match:
                return match.group(1)
            return self._currently_parsing_url

        # 2. Hard fallback to inspecting the active extractor if it *did* happen to load
        curr_ie = getattr(self, '_current_ie', None)
        if curr_ie and hasattr(curr_ie, '_current_video_id') and curr_ie._current_video_id:
            return curr_ie._current_video_id

        # 3. Last resort: scrape the warning/error text string
        return None


    def report_warning(self, message, only_once=False):
        """
        Print the message to stderr, it will be prefixed with 'WARNING:'
        If stderr is a tty file the 'WARNING:' will be colored
        """
        active_vid = self._get_active_video_id()
        if message == '[youtube] Video unavailable. This video has been removed by the uploader':
            # 2. Tell yt-dlp to immediately abandon this video and move on
            raise ExtractorError("[CustomDL] Video removed by uploader")
        if message in MESSAGES_TO_SKIP_PAST_AND_NOT_LOG:
            return
        if '[youtube] This live event will begin in' in message:
            return
        if self.params.get('logger') is not None:
            podcast_being_processed = YouTubePodcast.objects.all().filter(being_processed=True).first()
            if podcast_being_processed is not None:
                jon_stewart_common_data_retrieval_log_messages = (
                        '[youtube:tab] Incomplete data received. Retrying' in message or
                        '[youtube:tab] Incomplete data received. Giving up after 3 retries' in message
                )
                jon_stewart_being_processed = podcast_being_processed.name == 'The Weekly Show with Jon Stewart | FULL Episodes'
                jon_stewart_issue = jon_stewart_common_data_retrieval_log_messages and jon_stewart_being_processed

                trevor_noah_hidden_log_messages = (
                    '[youtube:tab] YouTube said: INFO - 2 unavailable videos are hidden'
                )
                trevor_noah_being_processed = podcast_being_processed.name == 'What Now With Trevor Noah - (Full Podcast Episodes)'
                trevor_noah_issue = trevor_noah_hidden_log_messages and trevor_noah_being_processed


                mehdi_hassan_common_data_retrieval_log_messages = (
                        '[youtube:tab] YouTube said: INFO - 1 unavailable video is hidden' in message or
                        '[youtube] Video unavailable. This video is private' in message or
                        "[youtube] Private video. Sign in if you've been granted access to this video." in message
                )
                mehdi_hasan_being_processed = podcast_being_processed.name == "We're Not Kidding with Mehdi & Friends"
                mehdi_hasan_issue = mehdi_hassan_common_data_retrieval_log_messages and mehdi_hasan_being_processed
                if jon_stewart_issue:
                    # https://github.com/yt-dlp/yt-dlp/issues/11930#issuecomment-2564490472
                    self.params['logger'].info(message)
                    return
                elif trevor_noah_issue or mehdi_hasan_issue:
                    self.params['logger'].info(message)
                    return

                else:
                    self.params['logger'].warning(f"warning below is for podcast [{podcast_being_processed.name}]")
        super().report_warning(message, only_once=only_once)

    def trouble(self, message=None, tb=None, is_error=True):
        video_unavailable = False
        podcast_being_processed = None
        log_level = error_logging_level
        active_vid = self._get_active_video_id()
        if message in MESSAGES_TO_SKIP_PAST_AND_NOT_LOG:
            return

        if sys.exc_info()[0]:
            exception = sys.exc_info()[1]
            if type(exception) is ExtractorError:
                private_video = (
                        "Private video. Sign in if you've been granted access to this video"
                        in exception.msg or
                        "Video unavailable. This video is private" in exception.msg
                )
                removed_video = (
                        "Video unavailable. This video has been removed by the uploader" in exception.msg or
                        '[CustomDL] Video removed by uploader' in exception.orig_msg
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

        if podcast_being_processed is None:
            podcast_being_processed = YouTubePodcast.objects.all().filter(being_processed=True).first()
        TroubleRecord(
            message=message, levelno=log_level, video_unavailable=video_unavailable,
            podcast=podcast_being_processed, video_id=active_vid
        ).save()
        return  # I decided I'd rather never call the super and instead look for more videos
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
            "ignore_no_formats_error": True,
            "outtmpl": '%(title)s.%(ext)s',  # done because if not specified, ytdlp adds the video ID to the filename
            "paths": {"home": f"{youtube_podcast.video_file_location}"},
            "download_archive": youtube_podcast.archive_file_location,  # done so that past downloaded videos
            # are not re-downloaded
            "sleep_interval_requests": 20,  # to avoid youtube trying to verify the requests are not coming from a bot
            "playlistend": youtube_podcast.index_range,
            "logger": Loggers.get_logger("youtube_dlp"),
            "ffmpeg_location": settings.FFMPEG_LOCATION_PATH,
            "js_runtimes": {'deno': {'path': settings.DENO_PATH}},
            "format_sort": ['vcodec:avc', 'res', 'acodec:aac'],  # needed cause of
            # https://github.com/yt-dlp/yt-dlp/issues/11177#issuecomment-2395588715
            "extractor_args": {"youtube": {"player_client": ["default", "-tv_simply"]}},  # fixing latest yt-dlp bug
            # with arg from https://github.com/yt-dlp/yt-dlp/issues/14456#issuecomment-3339654496
            "cookiefile" : os.environ.get('COOKIE_LOCATION', None),
            'format': 'bv+ba/b', # needed cause of https://github.com/yt-dlp/yt-dlp/issues/14462#issuecomment-3340774234

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
        os.makedirs(ARCHIVE_FOLDER_PATH, exist_ok=True)
        if os.path.exists(previous_video_file_location):
            os.rename(previous_video_file_location, youtube_podcast.video_file_location)
        if os.path.exists(previous_archive_file_location):
            os.rename(previous_archive_file_location, youtube_podcast.archive_file_location)

    delete_videos_that_are_not_properly_tracked(youtube_podcast)
    automatically_hide_videos(youtube_podcast)
    update_archive_file(youtube_podcast)
    generate_rss_file(youtube_podcast)
    youtube_podcast.being_processed = False
    youtube_podcast.save()
