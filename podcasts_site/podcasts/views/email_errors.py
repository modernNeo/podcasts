import os

from podcasts.models import YouTubeDLPWarnError, LoggingFilePath
from podcasts.views.Gmail import Gmail
from podcasts.views.setup_logger import error_logging_level, warn_logging_level


def email_errors():
    errors = YouTubeDLPWarnError.objects.all().filter(processed=False)
    video_unavailable_errors = errors.filter(video_unavailable=True)
    if len(video_unavailable_errors) > 0:
        video_unavailables = f"""
        Unavailable Videos:
        
        """
        podcast_displayed = []
        for video_unavailable_error in video_unavailable_errors:
            if video_unavailable_error.podcast.id not in podcast_displayed:
                video_unavailables += f"{video_unavailable_error.podcast.description}\n"
            video_unavailables += f"\nhttps://www.youtube.com/watch?v={video_unavailable_error.message}"
    else:
        video_unavailables = None
    body = f"{video_unavailables}" if video_unavailables else video_unavailables
    file_paths = LoggingFilePath.objects.all()[0]

    if len(errors.filter(levelno=error_logging_level)) > 0:
        number_of_errors = errors.filter(levelno=error_logging_level)
        gmail = Gmail()
        log_sent = []
        for error in errors:
            if file_paths.error_file_path in log_sent:
                error.processed = True
                error.save()
                continue
            log_sent.append(file_paths.error_file_path)
            gmail.send_email(
                subject=f"{number_of_errors} podcast WARNINGS", body=body, to_email=os.environ['TO_EMAIL'], to_name='modernNeo',
                attachments=[file_paths.debug_file_path, file_paths.warn_file_path, file_paths.error_file_path]
            )
            error.processed = True
            error.save()
        gmail.close_connection()
    elif len(errors.filter(levelno=warn_logging_level)) > 0:
        gmail = Gmail()
        log_sent = []
        number_of_warnings = errors.filter(levelno=warn_logging_level)
        for error in errors:
            if file_paths.error_file_path in log_sent:
                error.processed = True
                error.save()
                continue
            log_sent.append(file_paths.error_file_path)
            gmail.send_email(
                subject=f"{number_of_warnings} podcast WARNINGS", body=body,
                to_email=os.environ['TO_EMAIL'], to_name='modernNeo',
                attachments=[file_paths.debug_file_path, file_paths.warn_file_path, file_paths.error_file_path]
            )
            error.processed = True
            error.save()
        gmail.close_connection()