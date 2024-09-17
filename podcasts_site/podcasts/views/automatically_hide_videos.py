from podcasts.models import YouTubePodcastVideo


def automatically_hide_videos(youtube_podcast):
    YouTubePodcastVideo.objects.all().update(hide=False)
    groups = youtube_podcast.youtubepodcastvideogrouping_set.all().filter(podcast_video__hide=False)
    occurrences = []
    date_number_with_multiple_occurrences = []
    for group in groups:
        if group.grouping_number in date_number_with_multiple_occurrences:
            continue
        if group.grouping_number not in occurrences:
            occurrences.append(group.grouping_number)
        else:
            date_number_with_multiple_occurrences.append(group.grouping_number)

    videos = YouTubePodcastVideo.objects.all().filter(
        podcast__name=youtube_podcast.name,
        youtubepodcastvideogrouping__grouping_number__in=date_number_with_multiple_occurrences
    )
    substrings = youtube_podcast.youtubepodcasttitlesubstring_set.all().order_by('priority')
    ids_of_videos_to_hide = []
    for date_number_with_multiple_occurrence in date_number_with_multiple_occurrences:
        videos_on_same_day = {
            video.original_title: video for video in videos.filter(grouping_number=date_number_with_multiple_occurrence)
        }
        video_ids = [video.id for video in list(videos_on_same_day.values())]
        delete_rest_of_videos = False
        for substring in substrings:
            if delete_rest_of_videos:
                break
            for video_title_on_same_day in videos_on_same_day.keys():
                if not delete_rest_of_videos and substring.title_substring in video_title_on_same_day:
                    video_ids.remove(videos_on_same_day[video_title_on_same_day].id)
                    delete_rest_of_videos = True
        ids_of_videos_to_hide.extend(video_ids)
    YouTubePodcastVideo.objects.filter(id__in=ids_of_videos_to_hide).update(hide=True)
