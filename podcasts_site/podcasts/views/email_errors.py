import os

from podcasts.models import YouTubeDLPError
from podcasts.views.Gmail import Gmail


def email_errors():
    errors = YouTubeDLPError.objects.all().filter(processed=False)
    if len(errors) > 0:
        gmail = Gmail()
        log_sent = []
        for error in errors:
            if error.error_file_path in log_sent:
                error.processed = True
                error.save()
                continue
            log_sent.append(error.error_file_path)
            gmail.send_email(
                subject="podcast errors", body="look at attachments", to_email=os.environ['TO_EMAIL'], to_name='modernNeo',
                attachments=[error.debug_file_path, error.warn_file_path, error.error_file_path]
            )
            error.processed = True
            error.save()
        gmail.close_connection()