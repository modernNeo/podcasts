import os
from pathlib import Path

import yt_dlp
from django.conf import settings
from django.core.management import BaseCommand
from podgen import Podcast, Episode, Media, Person, Category

from podcasts.models import YouTubePodcast, RSS_FEED_FOLDER_NAME, ARCHIVE_FOLDER_NAME
from podcasts.views.YouTubeVideoPostProcessor import YouTubeVideoPostProcessor


class Command(BaseCommand):
    def handle(self, *args, **options):
        youtube_podcasts = YouTubePodcast.objects.all().filter(url__isnull=False)
        Path(
            f"{settings.MEDIA_ROOT}/{RSS_FEED_FOLDER_NAME}"
        ).mkdir(parents=True, exist_ok=True)
        Path(
            f"{settings.MEDIA_ROOT}/{ARCHIVE_FOLDER_NAME}"
        ).mkdir(parents=True, exist_ok=True)
        first_run = False
        for youtube_podcast in youtube_podcasts:
            youtube_podcast.being_processed = True
            youtube_podcast.save()
            if not youtube_podcast.name:
                youtube_podcast.name = "temp"
                first_run = True
            Path(youtube_podcast.video_file_location).mkdir(parents=True, exist_ok=True)
            try:
                def title_filter(info, *, incomplete):
                    title = info.get("title")
                    if (
                            youtube_podcast.title_substring is not None and
                            youtube_podcast.title_substring not in title):
                        return f"{title} is not needed"

                # I was previously utilizing the daterange filter, but I switched to playlistend cause when daterange is used, it will check the date of each video in the playlist cause there is no guarantee they are sorted by date and time
                # today = datetime.datetime.now()
                # date_start = (today - datetime.timedelta(days=youtube_podcast.range)).strftime("%Y%m%d")
                # date_end = (today + datetime.timedelta(days=1)).strftime("%Y%m%d")
                yt_opts = {
                    'verbose': False,
                    # "daterange": DateRange(date_start, date_end),
                    "match_filter": title_filter,
                    "outtmpl": '%(title)s.%(ext)s', # done because if not specified, ytdlp adds the video ID to the filename
                    "paths": {"home": youtube_podcast.video_file_location},
                    "download_archive": youtube_podcast.archive_file_location, # done so that past downloaded videos are not re-downloaded
                    "ignoreerrors": True, # helpful so that if one video has an issue, the rest will still be attempted to be downloaded
                    "sleep_interval_requests": 15, # to avoid youtube trying to verify the requests are not coming from a bot
                    "playlistend": youtube_podcast.index_range, # stop after the latest 40 videos in a playlist as some playlists contain 2000+ videos to sift through
                    "geo_bypass_country": youtube_podcast.country_code # sometimes the videos are reported "unavailable" due to the I.P. address of the host
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
                os.rename(previous_video_file_location, youtube_podcast.video_file_location)
                os.rename(previous_archive_file_location, youtube_podcast.archive_file_location)
            category = None
            try:
                category = Category(youtube_podcast.category)
            except ValueError:
                pass
            p = Podcast(
                name=youtube_podcast.name,
                description=youtube_podcast.description,
                image=youtube_podcast.image,
                website=youtube_podcast.url,
                language=youtube_podcast.language,
                authors=[Person(youtube_podcast.author)],
                category=category,
                explicit=False,
                episodes=[
                Episode(
                    title=episode.original_title,
                    media=Media(episode.get_location, size=episode.size),
                )
                for episode in youtube_podcast.youtubepodcastvideo_set.all()
            ]
            )
            p.rss_file(youtube_podcast.feed_file_location)
            print(f"done with {youtube_podcast.name}")
            youtube_podcast.being_processed = False
            youtube_podcast.save()
