import datetime
import os
from pathlib import Path

import yt_dlp
from django.core.management import BaseCommand
from podgen import Podcast, Episode as PodGenEpisode, Media as PodGenMedia
from yt_dlp import postprocessor
from yt_dlp.utils._utils import DateRange

from podcasts.models import YouTubePodcast, Episode


# playlists that can be automatically ingested cause there is a timestamp in the title
# LIVE NEWS: BC live streaming news at noon, 6pm and 11pm
## CBC Vancouver News at 6
# https://www.youtube.com/playlist?list=PLd9pLwfvcsdSXJufULeZqnduIJ1peUP3B
#  Bill Burr's the Monday Morning Podcast
## Thursday Afternoon Monday Morning Podcast 8-22-24
## Monday Morning Podcast 8-20-24
# https://www.youtube.com/@BillBurrOfficial/videos
#  The National | Full Show
# https://www.youtube.com/playlist?list=PLvntPLkd9IMcbAHH-x19G85v_RE-ScYjk
# Honestly with Bari Weiss
# https://www.youtube.com/playlist?list=PL8RMFyRb2PguHhsO2iYsmzn5v-5SXRv3_

class FilenameCollectorPP(postprocessor.common.PostProcessor):
    def __init__(self):
        super(FilenameCollectorPP, self).__init__(None)

    def run(self, information):
        filename = information['filename']
        first_slash = filename.index("/")+1
        second_slash = filename[first_slash:].index("/")
        show = filename[first_slash:second_slash + first_slash]
        podcast = YouTubePodcast.objects.all().filter(name=show).first()
        if podcast:
            start_of_date = first_slash + second_slash + 1
            number_of_digits_in_timestamp = 10
            number = filename[start_of_date:start_of_date+number_of_digits_in_timestamp]
            timestamp = information['release_timestamp'] if information['release_timestamp'] else information['timestamp']
            timestamp = datetime.datetime.fromtimestamp(timestamp)
            Episode(
                name=information['title'], description=information["description"], podcast=podcast,
                date=timestamp,
                number=int(number.replace("-","")), url=information['original_url'],
                image=information['thumbnail'], extension=filename[filename.rfind("."):]
            ).save()
        return [], information

class Command(BaseCommand):
    def handle(self, *args, **options):
        YouTubePodcast(
            name= "CBC Vancouver News at 6",
            url = "https://www.youtube.com/playlist?list=PLd9pLwfvcsdSXJufULeZqnduIJ1peUP3B",
            range=7, video_substring="CBC Vancouver News at 6",
            when_to_pull="19:30", description="CBC News"
        ).save()
        podcasts_to_inject = YouTubePodcast.objects.all().filter(url__isnull=False)
        filename_collector = FilenameCollectorPP()
        Path("assets/feed").mkdir(parents=True, exist_ok=True)
        Path("assets/archives").mkdir(parents=True, exist_ok=True)
        for podcast_to_inject in podcasts_to_inject:
            video_location = f"assets/videos/{podcast_to_inject.name}"
            archive_file_location = f"assets/archives/{podcast_to_inject.name}"
            feed_location = f"assets/feed/{podcast_to_inject.name}.xml"
            Path(video_location).mkdir(parents=True, exist_ok=True)
            try:
                def title_filter(info, *, incomplete):
                    title = info.get("title")
                    if (
                            podcast_to_inject.video_substring is not None and
                            podcast_to_inject.video_substring not in title):
                        return f"{title} is not needed"

                today = datetime.datetime.now()
                date_start = (today - datetime.timedelta(days=podcast_to_inject.range)).strftime("%Y%m%d")
                date_end = (today + datetime.timedelta(days=1)).strftime("%Y%m%d")
                yt_opts = {
                    'verbose': True,
                    "daterange": DateRange(date_start, date_end),
                    "match_filter": title_filter,
                    "outtmpl": '%(upload_date>%Y-%m-%d)s-%(title)s.%(ext)s',
                    "paths": {"home": video_location},
                    "download_archive" : archive_file_location,
                    "break_on_existing" : True,
                    # "skip_download" : True, # if doing debug
                }
                with yt_dlp.YoutubeDL(yt_opts) as ydl:
                    ydl.add_post_processor(filename_collector)
                    ydl.download(podcast_to_inject.url)
            except yt_dlp.utils.ExistingVideoReached:
                p = Podcast(
                    name=podcast_to_inject.name,
                    website=podcast_to_inject.url,
                    description=podcast_to_inject.description,
                    explicit=False
                )
                p.episodes = [
                    PodGenEpisode(
                        title=episode.name,
                        media=PodGenMedia(episode.get_location()),
                        summary=episode.description
                    )
                    for episode in podcast_to_inject.episode_set.all()
                ]
                p.rss_file(feed_location)
                print(f"done with {podcast_to_inject.name}")