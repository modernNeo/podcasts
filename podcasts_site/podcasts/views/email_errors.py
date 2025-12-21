import os

from podcasts.models import YouTubeDLPWarnError, LoggingFilePath, VideoWithNewDateFormat
from podcasts.views.Gmail import Gmail
from podcasts.views.setup_logger import error_logging_level, warn_logging_level


def email_errors():
    errors_and_warnings = YouTubeDLPWarnError.objects.all().filter(processed=False)

    video_unavailable_errors_and_warnings = errors_and_warnings.filter(video_unavailable=True)
    email_body = None
    if len(video_unavailable_errors_and_warnings) > 0:
        email_body = "Unavailable Videos:\n\n"
        podcast_displayed = []
        for video_unavailable_error in video_unavailable_errors_and_warnings:
            if video_unavailable_error.podcast.id not in podcast_displayed:
                name = video_unavailable_error.podcast.custom_name \
                    if video_unavailable_error.podcast.custom_name else video_unavailable_error.podcast.name
                email_body += f"{name}\n"
            email_body += f"\nhttps://www.youtube.com/watch?v={video_unavailable_error.video_id}"

    all_other_errors_and_warnings = errors_and_warnings.filter(video_unavailable=False)
    all_other_errors = all_other_errors_and_warnings.filter(levelno=error_logging_level)
    all_other_warnings = all_other_errors_and_warnings.filter(levelno=warn_logging_level)
    number_of_errors = all_other_errors.count()
    number_of_warnings = all_other_warnings.count()
    if len(all_other_errors) > 0:
        email_body = "Other Errors:\n\n"
        for all_other_error in all_other_errors:
            email_body += f"{all_other_error.message} for podcast {all_other_error.podcast}\n"
    if len(all_other_warnings) > 0:
        email_body = "Other Warnings:\n\n"
        for all_other_warning in all_other_warnings:
            email_body += f"{all_other_warning.message} for podcast {all_other_warning.podcast}\n\n"
    subject = ""
    invalid_dates = VideoWithNewDateFormat.objects.all()
    number_of_invalid_dates = invalid_dates.count()
    if number_of_invalid_dates > 0:
        subject = f"{number_of_invalid_dates} CBC videos with invalid date formats"
    if number_of_errors > 0:
        if number_of_invalid_dates > 0:
            subject += " and"
        subject += f"{number_of_errors} podcast error{'' if number_of_errors == 1 else 's'}"
    if number_of_invalid_dates > 0:
        email_body += "Invalid Dates on CBC Vancouver News Videos\n\n"
    for invalid_date in invalid_dates:
        email_body += f"{invalid_date.video_title}"
    if number_of_warnings > 0:
        if number_of_errors > 0:
            subject += " and"
        subject += f" {number_of_warnings} "
        if number_of_errors == 0:
            subject += "podcast "
        subject += f"warning{'' if number_of_warnings == 1 else 's'}"


    file_paths = LoggingFilePath.objects.all()[0]

    gmail = Gmail()
    if number_of_errors > 0 or number_of_warnings > 0:
        log_sent = []
        for error in errors_and_warnings:
            if file_paths.error_file_path in log_sent:
                error.processed = True
                error.save()
                continue
            log_sent.append(file_paths.error_file_path)
            gmail.send_email(
                subject=subject, body=email_body, to_email=os.environ['TO_EMAIL'], to_name='modernNeo',
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