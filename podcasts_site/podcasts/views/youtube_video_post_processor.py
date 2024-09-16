import os

from yt_dlp import postprocessor

from podcasts.models import YouTubePodcast, YouTubePodcastVideo, YouTubePodcastVideoGrouping
from podcasts.views.cbc_the_national_timestamp import get_cbc_the_national_timestamp, \
    video_has_national_in_first_chapter
from podcasts.views.cbc_vancouver_timestamp import is_cbc_vancouver_video, get_cbc_vancouver_timestamp
from podcasts.views.get_thumbnails import get_thumbnails
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers


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
            youtube_dlp_logger.info("######################################")
            youtube_dlp_logger.info(f"Starting Post-Processing video {full_path}")
            youtube_dlp_logger.info("######################################")
            current_file_name = full_path[slash_indices[number_of_slashes - 1] + 1:]
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] current_file_name={current_file_name}")
            cbc_vancouver_news_video = is_cbc_vancouver_video(current_file_name)
            if cbc_vancouver_news_video:
                timestamp = get_cbc_vancouver_timestamp(current_file_name)
            elif video_has_national_in_first_chapter(information):
                timestamp = get_cbc_the_national_timestamp(information)
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
            thumbnail = get_thumbnails(information)
            if podcast.information_last_updated is None or timestamp > podcast.information_last_updated:
                podcast.name = information['playlist']
                podcast.description = information['description']
                podcast.image = thumbnail
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
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[thumbnail]={thumbnail}")
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[filesize]={information.get('filesize', None)}")
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[filesize_approx]={information.get('filesize_approx', None)}")
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[duration]={information.get('duration', None)}")
            file_size = information.get('filesize', None)
            if not file_size:
                file_size = information.get('filesize_approx', None)
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
                grouping_number=grouping_release_stamp,url=information['original_url'], image=thumbnail,
                size=file_size,extension=new_file_name[index_of_last_period:], duration=information['duration']
            )
            youtube_podcast_video.save()
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] {youtube_podcast_video} saved")

            if cbc_vancouver_news_video:
                youtube_podcast_video_grouping = YouTubePodcastVideoGrouping(
                    grouping_number=grouping_release_stamp, podcast=podcast, podcast_video=youtube_podcast_video
                )
                youtube_podcast_video_grouping.save()
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] {youtube_podcast_video_grouping} saved")
        youtube_dlp_logger.info("######################################")
        youtube_dlp_logger.info(f"Finished Post-Processing video {full_path}")
        youtube_dlp_logger.info("######################################")
        return [], information
