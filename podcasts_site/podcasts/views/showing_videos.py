from podcasts.models import YouTubePodcast, CronSchedule, YouTubeVideo
from podcasts.views.delete_podcast import delete_podcast
from podcasts.views.generate_rss_file import generate_rss_file
from podcasts.views.reset_podcast import reset_podcast


def showing_videos(request):
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
            podcast.custom_name = request.POST['name'] \
                if (request.POST['name'] != podcast.name and request.POST['name'].strip() != '' ) \
                else None
            podcast.cbc_news = request.POST.get('cbc_news', False) == 'on'
            podcast.save()
    elif request.POST.get("action", False) == 'Delete':
        delete_podcast(request.POST['id'])
    elif request.POST.get("action", False) == "Reset":
        reset_podcast(request.POST['id'])
    elif request.POST.get("action", False) == 'delete_video':
        video = YouTubeVideo.objects.all().filter(id=int(request.POST['video_id'])).first()
        if video:
            video.delete()
            generate_rss_file(video.podcast)
    elif request.POST.get("action", False) == "Unhide" or request.POST.get("action", False) == "Hide":
        youtube_video = YouTubeVideo.objects.all().filter(id=int(request.POST['video_id'])).first()
        if youtube_video:
            youtube_video.manually_hide = request.POST.get("action", False) == "Hide"
            youtube_video.save()
            generate_rss_file(youtube_video.podcast)
    elif request.POST.get("action", False) == "update_cron":
        if cron_schedule is None:
            cron_schedule = CronSchedule()
        cron_schedule.hour = request.POST['hour']
        cron_schedule.minute = request.POST['minute']
        cron_schedule.save()
    return {
        "podcasts" : YouTubePodcast.objects.all().order_by("-id"),
        "cron_schedule" : cron_schedule
    }