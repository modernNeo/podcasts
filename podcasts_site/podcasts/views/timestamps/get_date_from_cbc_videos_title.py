from podcasts.models import VideoWithNewDateFormat, YouTubePodcast
from podcasts.views.pstdatetimefield import pstdatetime
from podcasts.views.setup_logger import Loggers

CBC_NEWS_TITLE_DATE_NORMALIZER = {
    "Sept.": "Sep",
    "Aug." : "Aug",
    "Sep." : "Sep",
    "Oct." : "Oct",
    "Nov." : "Nov"
}

def normalize_date_string(video_title_after_substring):
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
    for date in CBC_NEWS_TITLE_DATE_NORMALIZER.keys():
        if date in video_title_after_substring:
            youtube_dlp_logger.info(
                f"[youtube_video_post_processor.py normalize_date_string()] found string [{date}] in "
                f"video_title_after_substring [{video_title_after_substring}]"
            )
            video_title_after_substring = video_title_after_substring.replace(
                date, CBC_NEWS_TITLE_DATE_NORMALIZER[date]
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
    if timestamp is None:
        podcast_being_processed = YouTubePodcast.objects.all().filter(being_processed=True).first()
        VideoWithNewDateFormat(
            video_title = video_title_after_substring, podcast=podcast_being_processed
        ).save()
    return timestamp