from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management import BaseCommand

from podcasts.views.pull_latest_youtube_videos import pull_latest_youtube_videos


class Command(BaseCommand):
    def handle(self, *args, **options):
        scheduler = BlockingScheduler()
        print("starting scheduler")
        scheduler.add_job(func=pull_latest_youtube_videos, trigger='cron', hour=4, minute="30", timezone='Canada/Pacific')
        print("schedular started")
        scheduler.start()
