import os

from yt_dlp import postprocessor

from podcasts.models import YouTubePodcast, YouTubePodcastVideo, YouTubePodcastVideoGrouping
from podcasts.views.pstdatetimefield import pstdatetime

CBC_VANCOUVER_NEWS_PREFIX = 'CBC Vancouver News at '

class YouTubeVideoPostProcessor(postprocessor.common.PostProcessor):
    def __init__(self):
        super(YouTubeVideoPostProcessor, self).__init__(None)

    def run(self, information):
        full_path = information['filename']
        slash_indices = [index for index, character in enumerate(full_path) if character == "/"]
        number_of_slashes = len(slash_indices)
        podcast = YouTubePodcast.objects.all().filter(being_processed=True).first()
        if podcast:
            current_file_name = full_path[slash_indices[number_of_slashes - 1] + 1:]
            if CBC_VANCOUVER_NEWS_PREFIX in current_file_name[:len(CBC_VANCOUVER_NEWS_PREFIX)]:
                # have to do something special for CBC just cause they have an 11 pm news program that gets a timestamp
                # that is set for the next day instead
                try:
                    index_of_colon = current_file_name.index(":")
                except ValueError:
                    index_of_colon = current_file_name.index("：")
                date_from_file_name = current_file_name[len(CBC_VANCOUVER_NEWS_PREFIX):index_of_colon]
                try:
                    timestamp = pstdatetime.strptime(date_from_file_name, "%I, %b %d")
                except ValueError:
                    timestamp = pstdatetime.strptime(date_from_file_name, "%I%M, %b %d")
                timestamp = pstdatetime(year=pstdatetime.now().year, month=timestamp.month, day=timestamp.day,
                                        hour=timestamp.hour+12,minute=timestamp.minute, second=0,
                                        tzinfo=pstdatetime.PACIFIC_TZ)
            else:
                timestamp = pstdatetime.from_epoch(
                    information['release_timestamp'] if information['release_timestamp'] else information['timestamp']
                )
            if podcast.information_last_updated is None or timestamp > podcast.information_last_updated:
                podcast.name = information['playlist']
                podcast.description = information['description']
                podcast.image = information['thumbnail']
                podcast.language = "en-US"
                podcast.author = information['uploader']
                podcast.category = information['categories'][0]
                podcast.information_last_updated = timestamp
                podcast.save()

            new_file_name = f"{timestamp.strftime('%Y-%m-%d-%H-%M')}-{current_file_name}"
            old_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{current_file_name}"
            new_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{new_file_name}"
            os.rename(old_file_path, new_file_path)
            release_stamp = int(timestamp.strftime('%Y-%m-%d-%H-%M').replace("-", ""))
            grouping_release_stamp = int(timestamp.strftime('%Y-%m-%d').replace("-", ""))

            youtube_podcast_video = YouTubePodcastVideo(
                filename=new_file_name, original_title=information['title'], description=information["description"],
                podcast=podcast, date=timestamp, identifier_number=release_stamp,
                grouping_number=grouping_release_stamp,url=information['original_url'], image=information['thumbnail'],
                size=information['filesize'],extension=new_file_name[new_file_name.rfind("."):]
            )
            youtube_podcast_video.save()

            YouTubePodcastVideoGrouping(
                grouping_number=grouping_release_stamp, podcast=podcast, podcast_video=youtube_podcast_video
            ).save()

        return [], information
