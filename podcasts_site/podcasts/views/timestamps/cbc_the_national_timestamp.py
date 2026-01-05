from podcasts.views.timestamps.cbc_vancouver_timestamp import get_date_from_cbc_videos_title
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers

THE_NATIONAL_DATE_FORMAT = ["%B %d, %Y", "%b %d, %Y"]
THE_NATIONAL_CHAPTER_PREFIX = 'The National for '


def video_has_national_in_first_chapter(information):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    if information.get('chapters', None) is None:
        youtube_dlp_logger.info(
            "[cbc_the_national_timestamp.py video_has_national_in_first_chapter()] could not detect 'chapters' in"
            " information"
        )
        return False
    chapters = information['chapters']
    if len(chapters) < 1:
        youtube_dlp_logger.info(
            "[cbc_the_national_timestamp.py video_has_national_in_first_chapter()] did not find at least 1 chapter"
        )
        return False
    first_chapter = information['chapters'][0]
    if first_chapter.get('title', None) is None:
        youtube_dlp_logger.info(
            f"[cbc_the_national_timestamp.py video_has_national_in_first_chapter()] did not find 'title' in "
            f"[{first_chapter}]"
        )
        return False
    is_national = (
            THE_NATIONAL_CHAPTER_PREFIX == first_chapter['title'][:len(THE_NATIONAL_CHAPTER_PREFIX)]
    )
    youtube_dlp_logger.info(
        f"[cbc_the_national_timestamp.py video_has_national_in_first_chapter()] first_chapter[title]="
        f"[{first_chapter['title']}]"
    )
    youtube_dlp_logger.info(
        f"[cbc_the_national_timestamp.py video_has_national_in_first_chapter()] is_national=[{is_national}]"
    )
    return is_national

def get_cbc_the_national_timestamp(information):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    date_string = information['chapters'][0]['title'][len(THE_NATIONAL_CHAPTER_PREFIX):]
    timestamp = get_date_from_cbc_videos_title(date_string, THE_NATIONAL_DATE_FORMAT)
    if timestamp is None:
        raise AttributeError()
    youtube_dlp_logger.info(f"[cbc_the_national_timestamp.py get_cbc_the_national_timestamp()] timestamp=[{timestamp}]")
    timestamp = pstdatetime(
        year=timestamp.year, month=timestamp.month, day=timestamp.day, hour=6 + 12,
        minute=1, # adding a minute just so that it's easier to make sure the national shows up after the vancouver
        # news in my queue.
        second=0, tzinfo=pstdatetime.PACIFIC_TZ
    )
    youtube_dlp_logger.info(f"[cbc_the_national_timestamp.py get_cbc_the_national_timestamp()] timestamp=[{timestamp}]")
    return timestamp