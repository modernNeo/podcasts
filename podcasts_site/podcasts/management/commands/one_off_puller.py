from django.core.management import BaseCommand

from podcasts.views.pull_latest_youtube_videos import pull_latest_youtube_videos


class Command(BaseCommand):
    def handle(self, *args, **options):
        pull_latest_youtube_videos()