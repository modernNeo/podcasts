import logging

from django.conf import settings
from django.core.exceptions import AppRegistryNotReady


class YoutubeDLPErrorHandler(logging.StreamHandler):

    def __init__(self, stream=None, debug_file_name=None, info_file_name=None, warn_file_name=None, error_file_name=None):
        self.debug_file_name = debug_file_name
        self.info_file_name = info_file_name
        self.warn_file_name = warn_file_name
        self.error_file_name = error_file_name
        super().__init__(stream)

    def emit(self, record):
        message = record.exc_text if record.exc_text is not None else record.msg
        request = str(record.__dict__)
        try:
            from podcasts.models import YouTubeDLPError
            # if len(YouTubeDLPError.objects.all().filter(message=message).exclude(fixed=True)) == 0:
            YouTubeDLPError(
                error_file_path=self.error_file_name, warn_file_path=self.warn_file_name,
                debug_file_path=self.debug_file_name, message=message, request=request).save()
        except AppRegistryNotReady:
            pass
        except Exception as e:
            if settings.PROD_ENV:
                raise e
        super().emit(record)
