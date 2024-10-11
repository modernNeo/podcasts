from podcasts.models import YouTubePodcast, YouTubeVideo


def automatically_hide_videos(youtube_podcast: YouTubePodcast):
    groups = youtube_podcast.podcastvideogrouping_set.all().filter(podcast_video__hide=False)
    occurrences = []
    date_number_with_multiple_occurrences = []
    for group in groups:
        if group.grouping_number in date_number_with_multiple_occurrences:
            continue
        if group.grouping_number not in occurrences:
            occurrences.append(group.grouping_number)
        else:
            date_number_with_multiple_occurrences.append(group.grouping_number)

    videos = YouTubeVideo.objects.all().filter(
        podcast__name=youtube_podcast.name,
        podcastvideogrouping__grouping_number__in=date_number_with_multiple_occurrences
    )
    prefixes = youtube_podcast.youtubepodcasttitleprefix_set.all().order_by('priority')
    ids_of_videos_to_hide = []
    for date_number_with_multiple_occurrence in date_number_with_multiple_occurrences:
        videos_on_same_day = {
            video.original_title: video for video in videos.filter(grouping_number=date_number_with_multiple_occurrence)
        }
        video_ids = [video.id for video in list(videos_on_same_day.values())]
        delete_rest_of_videos = False
        for prefix in prefixes:
            if delete_rest_of_videos:
                break
            for video_title_on_same_day in videos_on_same_day.keys():
                if not delete_rest_of_videos and video_title_on_same_day[:len(prefix.title_prefix)] == prefix.title_prefix:
                    video_ids.remove(videos_on_same_day[video_title_on_same_day].id)
                    delete_rest_of_videos = True
        ids_of_videos_to_hide.extend(video_ids)
    YouTubeVideo.objects.filter(id__in=ids_of_videos_to_hide).update(hide=True)
