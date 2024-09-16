from django.conf import settings

from podcasts.views.cbc_vancouver_timestamp import get_date_from_cbc_videos_title
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers


def video_has_national_in_first_chapter(information):
    if information.get('chapters', None) is None:
        return False
    chapters = information['chapters']
    if len(chapters) < 1:
        return False
    first_chapter = information['chapters'][0]
    if first_chapter.get('title', None) is None:
        return False
    is_national = settings.THE_NATIONAL_CHAPTER_PREFIX == first_chapter['title'][:len(settings.THE_NATIONAL_CHAPTER_PREFIX)]
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    youtube_dlp_logger.info(
        f"[youtube_video_post_processor.py video_has_national_in_first_chapter()] first_chapter[title]=[{first_chapter['title']}]"
    )
    youtube_dlp_logger.info(
        f"[youtube_video_post_processor.py video_has_national_in_first_chapter()] is_national=[{is_national}]"
    )
    return is_national

def get_cbc_the_national_timestamp(information):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    date_string = information['chapters'][0]['title'][len(settings.THE_NATIONAL_CHAPTER_PREFIX):]
    timestamp = get_date_from_cbc_videos_title(date_string, settings.THE_NATIONAL_DATE_FORMAT)
    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp=[{timestamp}]")
    timestamp = pstdatetime(year=pstdatetime.now().year, month=timestamp.month, day=timestamp.day,
                            hour=6 + 12, minute=0, second=0,
                            tzinfo=pstdatetime.PACIFIC_TZ)
    return timestamp