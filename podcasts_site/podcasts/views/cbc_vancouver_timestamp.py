from django.conf import settings

from podcasts.views.get_date_from_cbc_videos_title import get_date_from_cbc_videos_title
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers


def is_cbc_vancouver_video(current_file_name):
    return settings.CBC_VANCOUVER_NEWS_PREFIX == current_file_name[:len(settings.CBC_VANCOUVER_NEWS_PREFIX)]

def get_cbc_vancouver_timestamp(current_file_name):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
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
                            hour=timestamp.hour + 12, minute=timestamp.minute, second=0,
                            tzinfo=pstdatetime.PACIFIC_TZ)
    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp={timestamp}")
    return timestamp