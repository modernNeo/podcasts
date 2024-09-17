from podcasts.views.timestamps.cbc_the_national_timestamp import video_has_national_in_first_chapter, \
    get_cbc_the_national_timestamp
from podcasts.views.timestamps.cbc_vancouver_timestamp import is_cbc_vancouver_video, get_cbc_vancouver_timestamp
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers


def get_timestamp(information, current_file_name):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    cbc_vancouver_news_video = is_cbc_vancouver_video(current_file_name)
    if cbc_vancouver_news_video:
        timestamp = get_cbc_vancouver_timestamp(current_file_name).pst
    elif video_has_national_in_first_chapter(information):
        timestamp = get_cbc_the_national_timestamp(information).pst
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