from podcasts.views.timestamps.get_date_from_cbc_videos_title import get_date_from_cbc_videos_title
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers

CBC_VANCOUVER_NEWS_PREFIX = 'CBC Vancouver News at '

CBC_VANCOUVER_NEWS_DATE_FORMAT = [
    "%I, %b %d", "%I%M, %b %d", "%I, %B %d",
    "%I,%B %d", # needed cause of a typo with 2024 July 14's title
    "%I_%M %p, %B %d", #needed cause of a wierd format with the videos around 2024 July 3rd
    "%I%M %p, %B %d", #needed cause of wierd format with the videos around 2024 June 22nd
    "%I_%M, %B %d", # needed cause of a wierd format on July 20th
    "%I %b %d", # used on 2024 Oct 9th at the earliest
    "%I, %b%d", # used on 2024 Oct 11th at the earliest
    "%I_%M,%b%d", # used on 2024 Oct 19th at the earliest
    "%I_%M, %b %d", # used for 2024 Oct 26th
    "%I,%b %d", # used for 2024 Nov 3rd
    "%I%M %b %d", # used on 2024 Nov 9th
    "%I_%M %b %d", #used on 2024 Nov 16
    "%I%M, %B %d", # used for 2025 March 29th
    "%I_%M,%B %d", # used on 2025 April 26
    "%I.%B %d", # used on 2025 May 2nd
    "%I - %b %d", # used on 2025 May 5th
    "%I%M%p %b %d", # used on 2025 May 10th
    "%I_%M%p, %B %d", # used on 2025 July 5th
    "%I%p, %B %d", #used on 2025 July 3rd and 4th
    "%I %B %d", #used on 2025, July 7th
    "%I %b%d", #used on 2025, Sept 1
]

def is_cbc_vancouver_video(current_file_name):
    is_cbc_vancouver = (
            CBC_VANCOUVER_NEWS_PREFIX == current_file_name[:len(CBC_VANCOUVER_NEWS_PREFIX)]
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
    title_substring_with_date = current_file_name[len(CBC_VANCOUVER_NEWS_PREFIX):]
    youtube_dlp_logger.info(
        f"[cbc_vancouver_timestamp.py get_cbc_vancouver_timestamp()] passing the substring "
        f"[{title_substring_with_date}] instead of [{current_file_name}] to get_date_from_cbc_videos_title"
    )
    timestamp = get_date_from_cbc_videos_title(title_substring_with_date, CBC_VANCOUVER_NEWS_DATE_FORMAT)
    youtube_dlp_logger.info(f"[cbc_vancouver_timestamp.py get_cbc_vancouver_timestamp()] timestamp=[{timestamp}]")
    if timestamp:
        # necessary because just using the hour that is extracted from the title of the video makes it seem like a video that
        # was uploaded at 6 PM was instead uploaded at 6 AM
        hour = timestamp.hour + 12 if timestamp.hour + 12 <= 23 else timestamp.hour

        timestamp = pstdatetime(year=pstdatetime.now().year, month=timestamp.month, day=timestamp.day,
                                hour=hour, minute=timestamp.minute, second=0,
                                tzinfo=pstdatetime.PACIFIC_TZ)
        youtube_dlp_logger.info(f"[cbc_vancouver_timestamp.py get_cbc_vancouver_timestamp()] timestamp={timestamp}")
    return timestamp