from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management import BaseCommand

from podcasts.models import CronSchedule
from podcasts.views.pull_latest_youtube_videos import pull_latest_youtube_videos


class Command(BaseCommand):
    def handle(self, *args, **options):
        scheduler = BlockingScheduler()
        print("starting scheduler")
        schedule = CronSchedule.objects.all().first()
        if schedule:
            scheduler.add_job(
                func=pull_latest_youtube_videos, trigger='cron', hour=schedule.hour, minute=schedule.minute,
                timezone='Canada/Pacific'
            )
            print("schedular started")
            scheduler.start()
        else:
            print("no schedule found")
