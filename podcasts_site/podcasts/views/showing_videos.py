from django.db.models import Q

from podcasts.models import YouTubePodcast, CronSchedule, DuplicatePodcastVideo, PodcastVideo
from podcasts.views.delete_podcast import delete_podcast
from podcasts.views.generate_rss_file import generate_rss_file
from podcasts.views.reset_podcast import reset_podcast


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
        video = PodcastVideo.objects.all().filter(id=int(request.POST['video_id'])).first()
        if video:
            video.delete()
            generate_rss_file(video.podcast)
    elif request.POST.get("action", False) == 'delete_duplicate_video':
        video = DuplicatePodcastVideo.objects.all().filter(id=int(request.POST['video_id'])).first()
        if video:
            video.delete()
    elif request.POST.get("action", False) == "Unhide" or request.POST.get("action", False) == "Hide":
        youtube_video = PodcastVideo.objects.all().filter(id=int(request.POST['video_id'])).first()
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
    podcasts = []
    for youtube_podcast in YouTubePodcast.objects.all().order_by("-id"):
        if youtube_podcast.cbc_news:
            videos = list(youtube_podcast.cbcnewspodcastvideo_set.all())
            videos.extend(youtube_podcast.duplicatepodcastvideo_set.all())
        else:
            videos = list(youtube_podcast.podcastvideo_set.all())
        videos.sort(key=lambda x: x.identifier_number, reverse=True)
        if show_hidden:
            if youtube_podcast.cbc_news:
                total_episodes = youtube_podcast.cbcnewspodcastvideo_set.all().count()
                total_episodes += youtube_podcast.duplicatepodcastvideo_set.all().count()
            else:
                total_episodes = youtube_podcast.podcastvideo_set.all().count()
        else:
            if youtube_podcast.cbc_news:
                total_episodes = youtube_podcast.cbcnewspodcastvideo_set.all().exclude(
                    Q(hide=True) | Q(manually_hide=True)
                ).count()
                total_episodes += youtube_podcast.duplicatepodcastvideo_set.all().exclude(
                    Q(hide=True) | Q(manually_hide=True)
                ).count()
            else:
                total_episodes = youtube_podcast.podcastvideo_set.all().exclude(
                    Q(hide=True) | Q(manually_hide=True)
                ).count()
        podcasts.append({
            "podcast" : youtube_podcast,
            "videos" : videos,
            "stats" : {
                "shown" : total_episodes if total_episodes <= 3 else 3,
                "total" : total_episodes
            }
        })
    return {
        "podcasts" : podcasts,
        "cron_schedule" : cron_schedule
    }