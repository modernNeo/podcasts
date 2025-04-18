from datetime import timedelta

from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers
from podcasts.views.timestamps.cbc_the_national_timestamp import video_has_national_in_first_chapter, \
    get_cbc_the_national_timestamp
from podcasts.views.timestamps.cbc_vancouver_timestamp import is_cbc_vancouver_video, get_cbc_vancouver_timestamp


def get_timestamp(information, current_file_name, podcast_being_processed):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    cbc_vancouver_news_video = is_cbc_vancouver_video(current_file_name)
    the_national_video = video_has_national_in_first_chapter(information)
    if cbc_vancouver_news_video:
        file_name_timestamp = get_cbc_vancouver_timestamp(current_file_name).pst
        video_timestamp = pstdatetime.from_epoch(int(information['timestamp'])).pst
        if video_timestamp.hour < 3:
            video_timestamp = video_timestamp - timedelta(hours=6)
        timestamp = pstdatetime(
            year=video_timestamp.year, month=video_timestamp.month, day=video_timestamp.day,
            hour=file_name_timestamp.hour, minute=file_name_timestamp.minute,
            second=0, tzinfo=pstdatetime.PACIFIC_TZ
        )
    elif the_national_video or podcast_being_processed.name == 'The National | Full Show':
        manually_extract = not the_national_video
        if the_national_video:
            try:
                timestamp = get_cbc_the_national_timestamp(information).pst
            except AttributeError:
                manually_extract = True # some videos have the day in a format like "July 2024" in the chapter
                # so I have to manually extract even though the chapter technically had 'The National' in it
        if manually_extract:
            video_timestamp = pstdatetime.from_epoch(int(information['timestamp']))
            if video_timestamp.hour < 3: # decided that if a video is uploaded in the first 3 hours of  day, to assume
                # it was from the previous day
                video_timestamp = video_timestamp - timedelta(hours=6)
            timestamp = pstdatetime(
                year=video_timestamp.year, month=video_timestamp.month, day=video_timestamp.day, hour=6 + 12,
                minute=1, # adding a minute just so that it's easier to make sure the national shows up after the
                # vancouver news in my queue.
                second=0,tzinfo=pstdatetime.PACIFIC_TZ
            )

    else:
        youtube_dlp_logger.info(
            f"[get_timestamp.py get_timestamp()] "
            f"information[release_timestamp]={information.get('information', None)}"
        )
        youtube_dlp_logger.info(
            f"[get_timestamp.py get_timestamp()] "
            f"information[timestamp]={information.get('timestamp', None)}"
        )
        timestamp = pstdatetime.from_epoch(
            information['release_timestamp'] if information['release_timestamp'] else information['timestamp']
        ).pst
    return timestamp, cbc_vancouver_news_video