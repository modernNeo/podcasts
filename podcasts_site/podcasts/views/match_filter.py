from podcasts.models import YouTubePodcast


def match_filter(info, *, incomplete):
    title = info.get("title")
    if title is None:
        # it's processing the podcast info
        return
    if info['live_status'] == 'is_upcoming':
        # processing a video that is not yet uploaded
        return f"{title} is not yet uploaded"
    youtube_podcast = YouTubePodcast.objects.all().filter(being_processed=True).first()
    if youtube_podcast:
        substrings = list(
            youtube_podcast.youtubepodcasttitlesubstring_set.all()
            .values_list('title_substring', flat=True)
        )
        prefixes = list(
            youtube_podcast.youtubepodcasttitleprefix_set.all()
            .values_list('title_prefix', flat=True)
        )
        if len(substrings) > 0 or len(prefixes) > 0:
            matches_substring_filter = [
                1
                for substring in substrings
                if substring in title
            ]
            matches_prefix_filter = [
                1 for prefix in prefixes
                if title[:len(prefix)] == prefix
            ]
            if len(matches_substring_filter) > 0:
                pass  # keep it
            if len(matches_prefix_filter) > 0:
                pass  # keep it
            else:
                return f"{title} is not needed"