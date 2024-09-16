import os

from django.conf import settings
from yt_dlp import postprocessor

from podcasts.models import YouTubePodcast, YouTubePodcastVideo, YouTubePodcastVideoGrouping
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers

def normalize_date_string(video_title_after_substring):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    for date in settings.CBC_NEWS_TITLE_DATE_NORMALIZER.keys():
        if date in video_title_after_substring:
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py normalize_date_string()] found string [{date}] in "
                f"video_title_after_substring [{video_title_after_substring}]"
            )
            video_title_after_substring = video_title_after_substring.replace(
                date, settings.CBC_NEWS_TITLE_DATE_NORMALIZER[date]
            )
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py normalize_date_string()] video_title_after_substring =  "
                f"[{video_title_after_substring}]"
            )
        else:
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py normalize_date_string()] did NOT find string [{date}] in "
                f"video_title_after_substring [{video_title_after_substring}]"
            )
    return video_title_after_substring


def get_date_from_cbc_videos_title(video_title_after_substring, date_formats):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    video_title_after_substring = normalize_date_string(video_title_after_substring)
    timestamp = None
    for date_format in date_formats:
        index = len(video_title_after_substring)
        while index > -1  and timestamp is None:
            try:
                date_substring = video_title_after_substring[:index]
                youtube_dlp_logger.info(
                    f"[youtube_video_post_processor.py get_date_from_cbc_videos_title()] matching string "
                    f"[{date_substring}] against format [{date_format}]"
                )
                timestamp = pstdatetime.strptime(date_substring, date_format)
            except ValueError:
                index -= 1
        if timestamp is not None:
            break
    youtube_dlp_logger.info(
        f"[youtube_video_post_processor.py get_date_from_cbc_videos_title()] returning timestamp [{timestamp}]"
    )
    return timestamp

def video_has_national_in_first_chapter(information):
    if information.get('chapters', None) is None:
        return False
    chapters = information['chapters']
    if len(chapters) < 1:
        return False
    first_chapter = information['chapters'][0]
    if first_chapter.get('title', None) is None:
        return False
    return settings.THE_NATIONAL_CHAPTER_PREFIX == first_chapter['title'][:len(settings.THE_NATIONAL_CHAPTER_PREFIX)]

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
            if settings.CBC_VANCOUVER_NEWS_PREFIX == current_file_name[:len(settings.CBC_VANCOUVER_NEWS_PREFIX)]:
                # have to do something special for CBC just cause they have an 11 pm news program that gets a timestamp
                # that is set for the next day instead
                title_substring_with_date = current_file_name[len(settings.CBC_VANCOUVER_NEWS_PREFIX):]
                youtube_dlp_logger.info(
                    f"[youtube_video_post_processor.py run()] passing the substring [{title_substring_with_date}]"
                    f" instead of [{current_file_name}] to get_date_from_cbc_videos_title"
                )
                timestamp = get_date_from_cbc_videos_title(title_substring_with_date, settings.CBC_VANCOUVER_NEWS_DATE_FORMAT)
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp=[{timestamp}]")
                timestamp = pstdatetime(year=pstdatetime.now().year, month=timestamp.month, day=timestamp.day,
                                        hour=timestamp.hour+12,minute=timestamp.minute, second=0,
                                        tzinfo=pstdatetime.PACIFIC_TZ)
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp={timestamp}")
            elif video_has_national_in_first_chapter(information):
                date_string = information['chapters'][0]['title'][len(settings.THE_NATIONAL_CHAPTER_PREFIX):]
                timestamp = get_date_from_cbc_videos_title(date_string, settings.THE_NATIONAL_DATE_FORMAT)
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp=[{timestamp}]")
                timestamp = pstdatetime(year=pstdatetime.now().year, month=timestamp.month, day=timestamp.day,
                                        hour=6+12,minute=0, second=0,
                                        tzinfo=pstdatetime.PACIFIC_TZ)
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
            thumbnail = information.get('thumbnail', None)
            if thumbnail is None:
                pass
            if ".png" in thumbnail:
                thumbnail = thumbnail[:thumbnail.index(".png")+4]
            elif ".jpg" in thumbnail:
                thumbnail = thumbnail[:thumbnail.index(".jpg") + 4]
            else:
                thumbnail = None
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

            youtube_podcast_video_grouping = YouTubePodcastVideoGrouping(
                grouping_number=grouping_release_stamp, podcast=podcast, podcast_video=youtube_podcast_video
            )
            youtube_podcast_video_grouping.save()
            youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] {youtube_podcast_video_grouping} saved")
        youtube_dlp_logger.info("######################################")
        youtube_dlp_logger.info(f"Finished Post-Processing video {full_path}")
        youtube_dlp_logger.info("######################################")
        return [], information
