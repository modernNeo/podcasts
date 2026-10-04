from podcasts.models import RSSPodcastFeed
from podcasts.views.pull_latest_external_rss_feed import pull_latest_external_rss_feed


def pull_latest_external_rss_feeds():
    rss_podcast_feeds = RSSPodcastFeed.objects.all()
    for rss_podcast_feed in rss_podcast_feeds:
        pull_latest_external_rss_feed(rss_podcast_feed)