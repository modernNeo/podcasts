from django.conf import settings

from podcasts.views.timestamps.get_date_from_cbc_videos_title import get_date_from_cbc_videos_title
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers


def is_cbc_vancouver_video(current_file_name):
    is_cbc_vancouver = (
            settings.CBC_VANCOUVER_NEWS_PREFIX == current_file_name[:len(settings.CBC_VANCOUVER_NEWS_PREFIX)]
    )
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    youtube_dlp_logger.info(
        f"[cbc_vancouver_timestamp.py is_cbc_vancouver_video()] is_cbc_vancouver=[{is_cbc_vancouver}]"
    )
    return is_cbc_vancouver

def get_cbc_vancouver_timestamp(current_file_name):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    # have to do something special for CBC just cause they have an 11 pm news program that gets a timestamp
    # that is set for the next day instead
    title_substring_with_date = current_file_name[len(settings.CBC_VANCOUVER_NEWS_PREFIX):]
    youtube_dlp_logger.info(
        f"[cbc_vancouver_timestamp.py get_cbc_vancouver_timestamp()] passing the substring "
        f"[{title_substring_with_date}] instead of [{current_file_name}] to get_date_from_cbc_videos_title"
    )
    timestamp = get_date_from_cbc_videos_title(title_substring_with_date, settings.CBC_VANCOUVER_NEWS_DATE_FORMAT)
    youtube_dlp_logger.info(f"[cbc_vancouver_timestamp.py get_cbc_vancouver_timestamp()] timestamp=[{timestamp}]")
    timestamp = pstdatetime(year=pstdatetime.now().year, month=timestamp.month, day=timestamp.day,
                            hour=timestamp.hour + 12, minute=timestamp.minute, second=0,
                            tzinfo=pstdatetime.PACIFIC_TZ)
    youtube_dlp_logger.info(f"[cbc_vancouver_timestamp.py get_cbc_vancouver_timestamp()] timestamp={timestamp}")
    return timestamp