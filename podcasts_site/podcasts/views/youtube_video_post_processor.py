import os
import re

from yt_dlp import postprocessor

from podcasts.models import YouTubePodcast, YouTubePodcastVideo, YouTubePodcastVideoGrouping
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers

CBC_VANCOUVER_NEWS_PREFIX = 'CBC Vancouver News at '

def index_of_out_range(name, index):
    return len(name) >= abs(index)

def get_index_of_end_of_date(the_file_name):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    if ":" in the_file_name:
        youtube_dlp_logger.info("[youtube_video_post_processor.py get_index_of_end_of_date()] matched first if")
        index_of_separator = the_file_name.index(":")
    elif "：" in the_file_name:
        youtube_dlp_logger.info("[youtube_video_post_processor.py get_index_of_end_of_date()] matched second if")
        index_of_separator = the_file_name.index("：")
    elif "-" in the_file_name:
        youtube_dlp_logger.info("[youtube_video_post_processor.py get_index_of_end_of_date()] matched third if")
        index_of_separator = the_file_name.index("-")
    else:
        raise Exception(f"could not find a separator [: or -] in filename {the_file_name}")
    youtube_dlp_logger.info(
        f"[youtube_video_post_processor.py get_index_of_end_of_date()] index_of_separator={index_of_separator}"
    )
    number_of_spaces = 0
    while index_of_out_range(the_file_name, index_of_separator-number_of_spaces) and re.match("\d", the_file_name[index_of_separator-number_of_spaces]) is None:
        number_of_spaces -= 1
    if not index_of_out_range(the_file_name, index_of_separator-number_of_spaces) or re.match("\d", the_file_name[index_of_separator-number_of_spaces]) is None:
        raise Exception(f"could not find the end of the date in file_name [{the_file_name}]")

    youtube_dlp_logger.info(
        f"[youtube_video_post_processor.py get_index_of_end_of_date()] determined number of spaces to be"
        f" {number_of_spaces}"
    )
    number_of_spaces += 1
    youtube_dlp_logger.info("[youtube_video_post_processor.py run()] finding index of [:]")
    return index_of_separator + number_of_spaces

def get_date_from_string(date_from_file_name):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    date_from_file_name.replace("Sept.", "Sep")
    formats = ["%I, %b %d", "%I%M, %b %d", "%I, %B %d"]
    timestamp = None
    for date_format in formats:
        try:
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py get_date_from_string()] matching string [{date_from_file_name}] "
                f"against format [{date_format}]"
            )
            timestamp = pstdatetime.strptime(date_from_file_name, date_format)
            break
        except ValueError:
            pass
    if not timestamp:
        raise Exception(f"unable to find a format that matches [{date_from_file_name}]")
    return timestamp

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
            try:
                current_file_name = full_path[slash_indices[number_of_slashes - 1] + 1:]
                youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] current_file_name={current_file_name}")
                if CBC_VANCOUVER_NEWS_PREFIX == current_file_name[:len(CBC_VANCOUVER_NEWS_PREFIX)]:
                    # have to do something special for CBC just cause they have an 11 pm news program that gets a timestamp
                    # that is set for the next day instead
                    index_of_separator = get_index_of_end_of_date(current_file_name)
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] index_of_separator={index_of_separator}"
                    )
                    date_from_file_name = current_file_name[len(CBC_VANCOUVER_NEWS_PREFIX):index_of_separator]
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] date_from_file_name={date_from_file_name}")
                    timestamp = get_date_from_string(date_from_file_name)
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
            except Exception as e:
                youtube_dlp_logger.error(f"[youtube_video_post_processor.py run()] e={e}")
        youtube_dlp_logger.info("######################################")
        youtube_dlp_logger.info(f"Finished Post-Processing video {full_path}")
        youtube_dlp_logger.info("######################################")
        return [], information
