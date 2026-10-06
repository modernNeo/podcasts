from django.core.management import BaseCommand

from podcasts.models import LoggingFilePath, CustomList
from podcasts.views.email_errors import email_errors
from podcasts.views.generate_rss_file import generate_custom_list_rss_file
from podcasts.views.pull_latest_external_rss_feeds import pull_latest_external_rss_feeds
from podcasts.views.pull_latest_youtube_videos import pull_latest_youtube_videos


class Command(BaseCommand):
    def handle(self, *args, **options):
        LoggingFilePath.objects.all().delete()
        pull_latest_youtube_videos()
        pull_latest_external_rss_feeds()
        for custom_list in CustomList.objects.all():
            generate_custom_list_rss_file(custom_list.id)
        email_errors()