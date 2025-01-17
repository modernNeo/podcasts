import os

from podcasts.models import YouTubeDLPWarnError, LoggingFilePath
from podcasts.views.Gmail import Gmail
from podcasts.views.setup_logger import error_logging_level, warn_logging_level


def email_errors():
    errors = YouTubeDLPWarnError.objects.all().filter(processed=False)
    video_unavailable_errors = errors.filter(video_unavailable=True).exclude(video_id__isnull=True)
    if len(video_unavailable_errors) > 0:
        video_unavailables = "Unavailable Videos:\n\n"
        podcast_displayed = []
        for video_unavailable_error in video_unavailable_errors:
            if video_unavailable_error.podcast.id not in podcast_displayed:
                name = video_unavailable_error.podcast.custom_name \
                    if video_unavailable_error.podcast.custom_name else video_unavailable_error.podcast.name
                video_unavailables += f"{name}\n"
            video_unavailables += f"\nhttps://www.youtube.com/watch?v={video_unavailable_error.video_id}"
    else:
        video_unavailables = None
    subject = ""
    number_of_errors = errors.filter(levelno=error_logging_level).count()
    number_of_warnings = errors.filter(levelno=warn_logging_level).count()
    if number_of_errors > 0:
        subject = f"{number_of_errors} podcast error{'' if number_of_errors == 1 else 's'}"
    if number_of_warnings > 0:
        if number_of_errors > 0:
            subject += " and"
        subject += f" {number_of_warnings} "
        if number_of_errors == 0:
            subject += "podcast "
        subject += f"warning{'' if number_of_warnings == 1 else 's'}"


    body = f"{video_unavailables}" if video_unavailables else video_unavailables
    file_paths = LoggingFilePath.objects.all()[0]

    gmail = Gmail()
    if number_of_errors > 0 or number_of_warnings > 0:
        log_sent = []
        for error in errors:
            if file_paths.error_file_path in log_sent:
                error.processed = True
                error.save()
                continue
            log_sent.append(file_paths.error_file_path)
            gmail.send_email(
                subject=subject, body=body, to_email=os.environ['TO_EMAIL'], to_name='modernNeo',
                attachments=[file_paths.debug_file_path, file_paths.warn_file_path, file_paths.error_file_path]
            )
            error.processed = True
            error.save()
    else:
        gmail.send_email(
            subject="podcasts successfully polled", body="", to_email=os.environ['TO_EMAIL'], to_name='modernNeo',
            attachments=[file_paths.debug_file_path, file_paths.warn_file_path, file_paths.error_file_path]
        )
    gmail.close_connection()