import os

from querystring_parser import parser

from podcasts.models import YouTubePodcast, CronSchedule, YouTubeVideo, CustomList, CustomListEntry, RSSPodcastFeed
from podcasts.views.delete_podcast import delete_podcast
from podcasts.views.generate_rss_file import generate_rss_file, generate_custom_list_rss_file
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
            prune = request.POST['prune'].strip()
            prune = int(prune) if prune.isdigit() else None
            podcast.url = request.POST['url']
            podcast.index_range = None if len(index_range) == 0 else index_range
            podcast.when_to_pull = request.POST['when_to_pull']
            current_name = podcast.frontend_name
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
                        os.rename(current_archive_location, new_archive_location)
                    if os.path.exists(current_rss_feed_file_location):
                        os.rename(current_rss_feed_file_location, new_rss_feed_file_location)
                else:
                    podcast.custom_name = None
            elif prune:
                videos_to_prune = podcast.youtubevideo_set.order_by("date")[:prune]
                for video_to_prune in videos_to_prune:
                    video_to_prune.delete()
            podcast.cbc_news = request.POST.get('cbc_news', False) == 'on'
            podcast.youtube_id = request.POST.get('youtube_id', False) == 'on'
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
    elif request.POST.get("action", False) == "create_custom_list":
        custom_list = CustomList()
        post_dict = parser.parse(request.POST.urlencode())
        custom_list.name = request.POST['name']
        podcasts, rss_podcast_feeds = get_list_of_checked_podcasts(post_dict)
        if len(podcasts) > 0 or len(rss_podcast_feeds) > 0:
            custom_list.save()
            for podcast in podcasts:
                CustomListEntry(podcast=podcast, custom_list=custom_list).save()
            for rss_podcast_feed in rss_podcast_feeds:
                CustomListEntry(external_podcast=rss_podcast_feed, custom_list=custom_list).save()
            generate_custom_list_rss_file(custom_list.id)
    elif request.POST.get("action", False) == "delete_custom_list":
        post_dict = parser.parse(request.POST.urlencode())
        if 'custom_list_id' in post_dict:
            CustomList.objects.all().filter(id=post_dict['custom_list_id']).delete()
    elif request.POST.get("action", False) == "update_custom_list":
        post_dict = parser.parse(request.POST.urlencode())
        if 'custom_list_id' in post_dict:
            custom_list = CustomList.objects.all().filter(id=post_dict['custom_list_id']).first()
            podcasts, rss_podcast_feeds = get_list_of_checked_podcasts(post_dict)
            if len(podcasts) == 0 and len(rss_podcast_feeds) == 0:
                for podcast in custom_list.customlistentry_set.all():
                    podcast.delete()
            else:
                current_list_entries = custom_list.customlistentry_set.all()
                podcasts_current_list_entries = current_list_entries.filter(podcast__isnull=False)
                podcasts_current_list_entries_ids = list(podcasts_current_list_entries.values_list(
                    'podcast_id',flat=True ))
                external_current_list_entries = current_list_entries.filter(external_podcast__isnull=False)
                external_current_list_entries_ids = list(external_current_list_entries.values_list('podcast_id',flat=True))

                # delete current ones that were unchecked
                for current_list_entry in podcasts_current_list_entries:
                    if current_list_entry.podcast not in podcasts:
                        current_list_entry.delete()
                for current_list_entry in external_current_list_entries:
                    if current_list_entry.external_podcast not in rss_podcast_feeds:
                        current_list_entry.delete()

                # add new ones
                for podcast in podcasts:
                    if podcast.id not in podcasts_current_list_entries_ids:
                        CustomListEntry(podcast=podcast, custom_list=custom_list).save()
                for rss_podcast_feed in rss_podcast_feeds:
                    if rss_podcast_feed.id not in external_current_list_entries_ids:
                        CustomListEntry(external_podcast=rss_podcast_feed, custom_list=custom_list).save()
            generate_custom_list_rss_file(custom_list.id)
    elif request.POST.get("action", False) == "track_rss_feed":
        RSSPodcastFeed(url=request.POST['url']).save()
    elif request.POST.get("action", False) == "delete_rss_feed":
        RSSPodcastFeed(id=request.POST['rss_feed_id']).delete()

    custom_lists = []
    for custom_list in CustomList.objects.all():
        names = []
        for podcast in custom_list.customlistentry_set.all():
            podcast = podcast.podcast.frontend_name if podcast.podcast else podcast.external_podcast.name
            names.append(podcast)
        custom_lists.append({
            "list_info" : custom_list,
            "podcast_names" : names,
        })

    return {
        "custom_lists": custom_lists,
        "rss_podcast_feeds" : RSSPodcastFeed.objects.all(),
        "podcasts" : YouTubePodcast.objects.all().order_by("-id"),
        "cron_schedule" : cron_schedule
    }

def get_list_of_checked_podcasts(post_dict):
    if 'checked_podcasts' not in post_dict and 'checked_rss_podcast_feeds' not in post_dict:
        return []
    podcasts = []
    rss_podcast_feeds = []
    if 'checked_podcasts' in post_dict:
        list_of_checked_podcasts = post_dict['checked_podcasts']
        if type(list_of_checked_podcasts) is str:
            podcast = YouTubePodcast.objects.all().filter(id=list_of_checked_podcasts).first()
            if podcast:
                podcasts.append(podcast)
        else:
            for checked_podcast in list_of_checked_podcasts:
                podcast = YouTubePodcast.objects.all().filter(id=checked_podcast).first()
                if podcast:
                    podcasts.append(podcast)

    if 'checked_rss_podcast_feeds' in post_dict:
        list_of_checked_rss_podcast_feeds = post_dict['checked_rss_podcast_feeds']
        if type(list_of_checked_rss_podcast_feeds) is str:
            podcast = RSSPodcastFeed.objects.all().filter(id=list_of_checked_rss_podcast_feeds).first()
            if podcast:
                rss_podcast_feeds.append(podcast)
        else:
            for checked_rss_podcast_feed in list_of_checked_rss_podcast_feeds:
                podcast = RSSPodcastFeed.objects.all().filter(id=checked_rss_podcast_feed).first()
                if podcast:
                    rss_podcast_feeds.append(podcast)
    return podcasts, rss_podcast_feeds