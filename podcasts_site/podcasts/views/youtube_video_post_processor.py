import os

from yt_dlp import postprocessor

from podcasts.models import YouTubePodcast, YouTubePodcastVideo, YouTubePodcastVideoGrouping
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers

CBC_VANCOUVER_NEWS_PREFIX = 'CBC Vancouver News at '

class YouTubeVideoPostProcessor(postprocessor.common.PostProcessor):
    def __init__(self):
        super(YouTubeVideoPostProcessor, self).__init__(None)

    def run(self, information):
        full_path = information['filename']
        slash_indices = [index for index, character in enumerate(full_path) if character == "/"]
        number_of_slashes = len(slash_indices)
        podcast = YouTubePodcast.objects.all().filter(being_processed=True).first()
        youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
        if podcast:
            try:
                current_file_name = full_path[slash_indices[number_of_slashes - 1] + 1:]
                youtube_dlp_logger.error(f"[youtube_video_post_processor.py run()] current_file_name={current_file_name}")
                youtube_dlp_logger.warn(f"[youtube_video_post_processor.py run()] current_file_name={current_file_name}")
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] current_file_name={current_file_name}")
                if CBC_VANCOUVER_NEWS_PREFIX == current_file_name[:len(CBC_VANCOUVER_NEWS_PREFIX)]:
                    # have to do something special for CBC just cause they have an 11 pm news program that gets a timestamp
                    # that is set for the next day instead
                    try:
                        index_of_colon = current_file_name.index(":")
                    except ValueError:
                        index_of_colon = current_file_name.index("：")
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] index_of_colon={index_of_colon}")
                    date_from_file_name = current_file_name[len(CBC_VANCOUVER_NEWS_PREFIX):index_of_colon]
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] date_from_file_name={date_from_file_name}")
                    try:
                        timestamp = pstdatetime.strptime(date_from_file_name, "%I, %b %d")
                    except ValueError:
                        try:
                            timestamp = pstdatetime.strptime(date_from_file_name, "%I%M, %b %d")
                        except ValueError:
                            timestamp = pstdatetime.strptime(date_from_file_name, "%I, %B %d")
                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp={timestamp}")
                    timestamp = pstdatetime(year=pstdatetime.now().year, month=timestamp.month, day=timestamp.day,
                                            hour=timestamp.hour+12,minute=timestamp.minute, second=0,
                                            tzinfo=pstdatetime.PACIFIC_TZ)
                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp={timestamp}")

                else:
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] "
                        f"information[release_timestamp]={information.get('information', None)}"
                    )
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] "
                        f"information[timestamp]={information.get('timestamp', None)}"
                    )
                    timestamp = pstdatetime.from_epoch(
                        information['release_timestamp'] if information['release_timestamp'] else information['timestamp']
                    )
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] podcast.information_last_updated={podcast.information_last_updated}")
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp={timestamp}")
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] podcast.information_last_updated={podcast.information_last_updated}")
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
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] new_file_name={new_file_name}")
                old_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{current_file_name}"
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] old_file_path={old_file_path}")
                new_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{new_file_name}"
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] new_file_path={new_file_path}")

                os.rename(old_file_path, new_file_path)
                release_stamp = int(timestamp.strftime('%Y-%m-%d-%H-%M').replace("-", ""))
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] release_stamp={release_stamp}")
                grouping_release_stamp = int(timestamp.strftime('%Y-%m-%d').replace("-", ""))
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] grouping_release_stamp={grouping_release_stamp}")

                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[title]={information.get('title', None)}")
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[description]={information.get('description', None)}")
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] podcast={podcast}")
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[original_url]={information.get('original_url', None)}")
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[thumbnail]={information.get('thumbnail', None)}")
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[filesize]={information.get('filesize', None)}")
                index_of_last_period = new_file_name.rfind('.')
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] new_file_name.rfind(.)={index_of_last_period}")
                if index_of_last_period != -1:
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] new_file_name[new_file_name.rfind(.):]="
                        f"{new_file_name[index_of_last_period:]}"
                    )

                youtube_podcast_video = YouTubePodcastVideo(
                    video_id=information['id'],filename=new_file_name, original_title=information['title'],
                    description=information["description"], podcast=podcast, date=timestamp, identifier_number=release_stamp,
                    grouping_number=grouping_release_stamp,url=information['original_url'], image=information['thumbnail'],
                    size=information['filesize'],extension=new_file_name[index_of_last_period:]
                )
                youtube_podcast_video.save()
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] {youtube_podcast_video} saved")

                youtube_podcast_video_grouping = YouTubePodcastVideoGrouping(
                    grouping_number=grouping_release_stamp, podcast=podcast, podcast_video=youtube_podcast_video
                )
                youtube_podcast_video_grouping.save()
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] {youtube_podcast_video_grouping} saved")
            except Exception as e:
                youtube_dlp_logger.error(f"[youtube_video_post_processor.py run()] e={e}")
        return [], information
