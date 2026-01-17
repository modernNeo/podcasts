from django.core.management import BaseCommand

from podcasts.models import LoggingFilePath
from podcasts.views.email_errors import email_errors
from podcasts.views.pull_latest_youtube_videos import pull_latest_youtube_videos


class Command(BaseCommand):
    def handle(self, *args, **options):
        LoggingFilePath.objects.all().delete()
        pull_latest_youtube_videos()
        email_errors()