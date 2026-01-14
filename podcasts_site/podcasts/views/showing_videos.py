import os

from podcasts.models import YouTubePodcast, CronSchedule, YouTubeVideo
from podcasts.views.delete_podcast import delete_podcast
from podcasts.views.generate_rss_file import generate_rss_file
from podcasts.views.reset_podcast import reset_podcast
from podcasts.views.setup_logger import Loggers


def showing_videos(request):
    cron_schedule = CronSchedule.objects.all().first()
    youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
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
            current_name = podcast.name
            new_name = request.POST['name']
            name_changed = current_name != new_name and new_name.strip() != ''
            youtube_dlp_logger.info(f"{current_name=}")
            youtube_dlp_logger.info(f"{new_name=}")
            youtube_dlp_logger.info(f"{name_changed=}")
            if name_changed:
                current_video_file_location = podcast.video_file_location
                current_archive_location = podcast.archive_file_location
                current_rss_feed_file_location = podcast.feed_file_location
                youtube_dlp_logger.info(f"{current_video_file_location=}")
                youtube_dlp_logger.info(f"{current_archive_location=}")
                youtube_dlp_logger.info(f"{current_rss_feed_file_location=}")
                podcast.custom_name = new_name
                new_video_file_location = podcast.video_file_location
                new_archive_location = podcast.archive_file_location
                new_rss_feed_file_location = podcast.feed_file_location
                youtube_dlp_logger.info(f"{new_video_file_location=}")
                youtube_dlp_logger.info(f"{new_archive_location=}")
                youtube_dlp_logger.info(f"{new_rss_feed_file_location=}")
                new_name_usable = (
                        os.path.exists(current_video_file_location) and
                        not os.path.exists(new_video_file_location) and
                        not os.path.exists(new_archive_location) and
                        not os.path.exists(new_rss_feed_file_location)
                )
                youtube_dlp_logger.info(f"{new_name_usable=}")
                if new_name_usable:
                    os.rename(current_video_file_location, podcast.video_file_location)
                    if os.path.exists(current_archive_location):
                        os.rename(current_archive_location, podcast.archive_file_location)
                    if os.path.exists(current_rss_feed_file_location):
                        os.rename(current_rss_feed_file_location, podcast.feed_file_location)
                else:
                    podcast.custom_name = None
            podcast.cbc_news = request.POST.get('cbc_news', False) == 'on'
            podcast.save()
            generate_rss_file(podcast)
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
        video_id = request.POST['video_id']
        youtube_dlp_logger.info(f"processing video with ID of [{video_id}]")
        youtube_video = YouTubeVideo.objects.all().filter(id=int(video_id)).first()
        youtube_podcast = youtube_video.podcast
        if youtube_video:
            youtube_video.manually_hide = request.POST.get("action", False) == "Hide"
            youtube_dlp_logger.info(f"video [{youtube_video}] with id {video_id} is set as {'' if youtube_video.manually_hide else 'not '}hidden")
            youtube_video.save()
            youtube_podcast.refresh_from_db()
            generate_rss_file(youtube_podcast)
        else:
            youtube_dlp_logger.error(f"could not find a video with ID [{video_id}]")
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