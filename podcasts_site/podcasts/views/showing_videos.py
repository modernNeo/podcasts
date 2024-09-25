import os
import shutil

from django.conf import settings
from django.db.models import Q

from podcasts.models import YouTubePodcast, YouTubePodcastVideo, VIDEOS_FOLDER_NAME, ARCHIVE_FOLDER_NAME, CronSchedule
from podcasts.views.generate_rss_file import generate_rss_file


def showing_videos(request, show_hidden):
    cron_schedule = CronSchedule.objects.all().first()
    if request.POST.get("action", False) == "Create":
        index_range = request.POST['index_range'].strip()
        YouTubePodcast(
            url = request.POST['url'], index_range=None if len(index_range) == 0 else index_range,
            when_to_pull=request.POST['when_to_pull']
        ).save()
    elif request.POST.get("action", False) == "Update":
        podcast = YouTubePodcast.objects.all().filter(id=int(request.POST['id'])).first()
        if podcast:
            index_range = request.POST['index_range'].strip()
            podcast.url = request.POST['url']
            podcast.index_range = None if len(index_range) == 0 else index_range
            podcast.when_to_pull = request.POST['when_to_pull']
            podcast.save()
    elif request.POST.get("action", False) == "Unhide" or request.POST.get("action", False) == "Hide":
        youtube_video = YouTubePodcastVideo.objects.all().filter(id=int(request.POST['video_id'])).first()
        if youtube_video:
            youtube_video.manually_hide = request.POST.get("action", False) == "Hide"
            youtube_video.save()
            generate_rss_file(youtube_video.podcast)
    elif request.POST.get("action", False) == "Reset":
        podcast = YouTubePodcast.objects.all().filter(id=int(request.POST['id'])).first()
        if podcast:
            podcast.being_processed = False
            for video in podcast.youtubepodcastvideo_set.all():
                video.delete()
            podcast.save()
            try:
                shutil.rmtree(podcast.video_file_location)
            except FileNotFoundError:
                pass
            try:
                shutil.rmtree(f"{settings.MEDIA_ROOT}/{VIDEOS_FOLDER_NAME}/temp")
            except FileNotFoundError:
                pass
            try:
                os.remove(podcast.archive_file_location)
            except (FileNotFoundError, IsADirectoryError):
                pass
            try:
                os.remove(f"{settings.MEDIA_ROOT}/{ARCHIVE_FOLDER_NAME}/temp")
            except FileNotFoundError:
                pass
            try:
                os.remove(podcast.feed_file_location)
            except FileNotFoundError:
                pass
    elif request.POST.get("action", False) == "update_cron":
        if cron_schedule is None:
            cron_schedule = CronSchedule()
        cron_schedule.hour = request.POST['hour']
        cron_schedule.minute = request.POST['minute']
        cron_schedule.save()
    podcasts = []
    for youtube_podcast in YouTubePodcast.objects.all().order_by("-id"):
        if show_hidden:
            total_episodes = youtube_podcast.youtubepodcastvideo_set.all().count()
        else:
            total_episodes = youtube_podcast.youtubepodcastvideo_set.all().exclude(
                Q(hide=True) | Q(manually_hide=True)
            ).count()
        podcasts.append({
            "podcast" : youtube_podcast,
            "stats" : {
                "shown" : total_episodes if total_episodes <= 3 else 3,
                "total" : total_episodes
            }
        })
    return {
        "podcasts" : podcasts,
        "cron_schedule" : cron_schedule
    }