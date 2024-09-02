import os
import shutil

from podcasts.models import YouTubePodcast, YouTubePodcastVideo
from podcasts.views.generate_rss_file import generate_rss_file


def showing_videos(request, show_hidden):
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
            youtube_video.hide = request.POST.get("action", False) == "Hide"
            youtube_video.save()
            generate_rss_file(youtube_video.podcast)
    elif request.POST.get("action", False) == "Reset":
        podcast = YouTubePodcast.objects.all().filter(id=int(request.POST['id'])).first()
        if podcast:
            podcast.being_processed = False
            for video in podcast.youtubepodcastvideo_set.all():
                video.delete()
            podcast.save()
            shutil.rmtree(podcast.video_file_location)
            os.remove(podcast.archive_file_location)
            os.remove(podcast.feed_file_location)
    podcasts = []
    for youtube_podcast in YouTubePodcast.objects.all().filter():
        if show_hidden:
            total_episodes = youtube_podcast.youtubepodcastvideo_set.all().count()
        else:
            total_episodes = youtube_podcast.youtubepodcastvideo_set.all().filter(hide=False).count()
        podcasts.append({
            "podcast" : youtube_podcast,
            "stats" : {
                "shown" : total_episodes if total_episodes <= 3 else 3,
                "total" : total_episodes
            }
        })
    return {
        "podcasts" : podcasts
    }