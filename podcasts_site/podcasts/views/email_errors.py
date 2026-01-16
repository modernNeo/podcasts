import os

from podcasts.models import LoggingFilePath, VideoWithNewDateFormat, WarnStreamHandlerRecord, TroubleRecord
from podcasts.views.Gmail import Gmail
from podcasts.views.setup_logger import error_logging_level, warn_logging_level


def email_errors():
    troubles = TroubleRecord.objects.all()

    subject = ""
    email_body = ""

    invalid_dates = VideoWithNewDateFormat.objects.all()
    number_of_invalid_dates = invalid_dates.count()
    if number_of_invalid_dates > 0:
        subject = f"{number_of_invalid_dates} CBC videos with invalid date formats"
        email_body = "Invalid Dates on CBC Vancouver News Videos\n\n"
        for invalid_date in invalid_dates:
            email_body += f"{invalid_date.video_title}\n"

    unavailable_videos = troubles.filter(video_unavailable=True)

    if len(unavailable_videos) > 0:
        body_heading = "Unavailable Videos:\n\n"
        email_body = f"{email_body}{body_heading}" if email_body else body_heading
        podcast_displayed = []
        for unavailable_video in unavailable_videos:
            if unavailable_video.podcast.id not in podcast_displayed:
                email_body += (
                    f"{unavailable_video.podcast.frontend_name}: "
                    f"https://www.youtube.com/watch?v={unavailable_video.video_id}\n")

    other_troubles = troubles.filter(video_unavailable=False)

    other_trouble_errors = other_troubles.filter(levelno=error_logging_level)
    number_of_other_trouble_errors = other_trouble_errors.count()
    if number_of_other_trouble_errors > 0:
        subject_line = f'{number_of_other_trouble_errors} "other" podcast trouble error{'' if number_of_other_trouble_errors == 1 else 's'}'
        if subject:
            subject = f"{subject} {subject_line}"
        else:
            subject = subject_line
        body_heading = 'Other Trouble Errors:\n\n'
        email_body = f"{email_body}{body_heading}" if email_body else body_heading
        for other_trouble_error in other_trouble_errors:
            email_body += f"{other_trouble_error.message} for podcast {other_trouble_error.podcast}\n"

    other_trouble_warnings = other_troubles.filter(levelno=warn_logging_level)
    number_of_other_trouble_warnings = other_trouble_warnings.count()
    if number_of_other_trouble_warnings > 0:
        subject_line = f'{number_of_other_trouble_warnings} "other" podcast trouble warning{'' if number_of_other_trouble_warnings == 1 else 's'}'
        if subject:
            subject = f"{subject} {subject_line}"
        else:
            subject = subject_line

        body_heading = "Other Trouble Warnings:\n\n"
        email_body = f"{email_body}{body_heading}" if email_body else body_heading
        for other_trouble_warning in other_trouble_warnings:
            email_body += f"{other_trouble_warning.message} for podcast {other_trouble_warning.podcast}\n\n"


    warnings = WarnStreamHandlerRecord.objects.all()
    number_of_warnings = warnings.count()
    if number_of_warnings > 0:
        subject_line = f" {number_of_warnings} podcast warning{'' if number_of_warnings == 1 else 's'}"
        if subject:
            subject = f"{subject} {subject_line}"
        else:
            subject = subject_line

        body_heading = "Other Warnings:\n\n"
        email_body = f"{email_body}{body_heading}" if email_body else body_heading
        for warning in warnings:
            email_body += f"{warning.message} for podcast {warning.podcast}\n\n"

    file_paths = LoggingFilePath.objects.all()
    logs_to_send = []
    for file_path in file_paths:
        logs_to_send.append(file_path.error_file_path)
        logs_to_send.append(file_path.warn_file_path)
        logs_to_send.append(file_path.debug_file_path)

    gmail = Gmail()
    gmail.send_email(
        subject=subject if (len(subject) > 0) else "podcasts successfully polled",
        body=email_body if (len(email_body) > 0) else None,
        to_email=os.environ['TO_EMAIL'],
        to_name='modernNeo',
        attachments=logs_to_send
    )
    gmail.close_connection()