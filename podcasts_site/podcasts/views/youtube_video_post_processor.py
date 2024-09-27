import os

from django.db import IntegrityError
from yt_dlp import postprocessor

from podcasts.models import YouTubePodcast, YouTubePodcastVideo, YouTubePodcastVideoGrouping, string_cleaner, \
    DuplicateYouTubePodcastVideo
from podcasts.views.get_thumbnails import get_thumbnails
from podcasts.views.timestamps.get_timestamp import get_timestamp
from podcasts.views.setup_logger import Loggers


class YouTubeVideoPostProcessor(postprocessor.common.PostProcessor):
    def __init__(self):
        super(YouTubeVideoPostProcessor, self).__init__(None)

    def run(self, information):
        full_path = information['filename']
        slash_indices = [index for index, character in enumerate(full_path) if character == "/"]
        number_of_slashes = len(slash_indices)
        podcast_being_processed = YouTubePodcast.objects.all().filter(being_processed=True).first()
        youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
        if podcast_being_processed:
            youtube_dlp_logger.info("######################################")
            youtube_dlp_logger.info(f"Starting Post-Processing video {full_path}")
            youtube_dlp_logger.info("######################################")
            current_file_name = full_path[slash_indices[number_of_slashes - 1] + 1:]
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] current_file_name={current_file_name}")
            timestamp, cbc_vancouver_news_video = get_timestamp(information, current_file_name, podcast_being_processed)
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] podcast.information_last_updated={podcast_being_processed.information_last_updated}")
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp={timestamp}")
            thumbnail = get_thumbnails(information)
            if podcast_being_processed.information_last_updated is None or timestamp > podcast_being_processed.information_last_updated:
                podcast_being_processed.name = information['playlist']
                podcast_being_processed.description = information['description']
                podcast_being_processed.image = thumbnail
                podcast_being_processed.language = "en-US"
                podcast_being_processed.author = information['uploader']
                podcast_being_processed.category = information['categories'][0]
                podcast_being_processed.information_last_updated = timestamp
                podcast_being_processed.save()

            new_file_name = string_cleaner(
                f"{timestamp.strftime('%Y-%m-%d-%H-%M')}-{current_file_name}"
            )
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] new_file_name={new_file_name}")
            old_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{current_file_name}"
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] old_file_path={old_file_path}")
            new_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{new_file_name}"
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] new_file_path={new_file_path}")

            os.rename(old_file_path, new_file_path)
            release_stamp = int(timestamp.strftime('%Y-%m-%d-%H-%M').replace("-", ""))
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] release_stamp={release_stamp}")
            grouping_release_stamp = int(timestamp.strftime('%Y-%m-%d').replace("-", ""))
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] grouping_release_stamp={grouping_release_stamp}")

            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] information[title]={information.get('title', None)}")
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] information[description]={information.get('description', None)}")
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] podcast={podcast_being_processed}")
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] information[original_url]={information.get('original_url', None)}")
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[thumbnail]={thumbnail}")
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] information[filesize]={information.get('filesize', None)}")
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] information[filesize_approx]={information.get('filesize_approx', None)}")
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] information[duration]={information.get('duration', None)}")
            file_size = information.get('filesize', None)
            if not file_size:
                file_size = information.get('filesize_approx', None)
            index_of_last_period = new_file_name.rfind('.')
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py run()] new_file_name.rfind(.)={index_of_last_period}")
            if index_of_last_period != -1:
                youtube_dlp_logger.info(
                    f"[youtube_video_post_processor.py run()] new_file_name[new_file_name.rfind(.):]="
                    f"{new_file_name[index_of_last_period:]}"
                )

            youtube_podcast_video = YouTubePodcastVideo(
                video_id=information['id'], filename=new_file_name, original_title=information['title'],
                description=information["description"], podcast=podcast_being_processed, date=timestamp,
                identifier_number=release_stamp,
                grouping_number=grouping_release_stamp, url=information['original_url'], image=thumbnail,
                size=file_size, extension=new_file_name[index_of_last_period:], duration=information['duration']
            )
            try:
                youtube_podcast_video.save()
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] {youtube_podcast_video} saved")
                if cbc_vancouver_news_video:
                    youtube_podcast_video_grouping = YouTubePodcastVideoGrouping(
                        grouping_number=grouping_release_stamp, podcast=podcast_being_processed,
                        podcast_video=youtube_podcast_video
                    )
                    youtube_podcast_video_grouping.save()
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] {youtube_podcast_video_grouping} saved")
            except IntegrityError as e:
                youtube_dlp_logger.error(f"[youtube_video_post_processor.py run()]  integrity error of {e} with {full_path}")
                DuplicateYouTubePodcastVideo(
                    video_id=information['id'], filename=new_file_name, original_title=information['title'],
                    description=information["description"], podcast=podcast_being_processed, date=timestamp,
                    identifier_number=release_stamp,
                    grouping_number=grouping_release_stamp, url=information['original_url'], image=thumbnail,
                    size=file_size, extension=new_file_name[index_of_last_period:], duration=information['duration']
                ).save()
        youtube_dlp_logger.info("######################################")
        youtube_dlp_logger.info(f"Finished Post-Processing video {full_path}")
        youtube_dlp_logger.info("######################################")
        return [], information
