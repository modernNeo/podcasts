import datetime

import feedparser

from podcasts.models import RSSPodcastFeed, RssPodcastEpisode
from podcasts.views.generate_rss_file import generate_external_rss_feed_rss_file


def pull_latest_external_rss_feed(rss_podcast_feed: RSSPodcastFeed):
    parsed_feed = feedparser.parse(rss_podcast_feed.url)

    # 2. Initialize your podgen Podcast object
    rss_podcast_feed.name = parsed_feed.feed.get("title", "Unknown")
    rss_podcast_feed.description = parsed_feed.feed.get("subtitle", "Converted feed")
    rss_podcast_feed.language = "en"
    rss_podcast_feed.owner_email = parsed_feed['feed']['authors'][0]['email']
    rss_podcast_feed.owner_name = parsed_feed['feed']['authors'][0]['name']
    rss_podcast_feed.save()

    entries_dict = {
        episode.video_id: episode
        for episode in rss_podcast_feed.rsspodcastepisode_set.all()
    }

    # 3. Iterate through the external entries and add them as episodes
    for entry in parsed_feed.entries:
        if entry['id'] in entries_dict:
            continue
        episode = RssPodcastEpisode()
        episode.podcast = rss_podcast_feed
        episode.video_id = entry['id']
        episode.original_title = entry.get("title")
        episode.description = entry.get("summary", "")
        episode.image = entry['image']['href'] if 'image' in entry else parsed_feed['feed']['image']['href']
        episode.duration = int(entry['itunes_duration'])
        episode.date = datetime.datetime.strptime(entry.get("published"), "%a, %d %b %Y %H:%M:%S %z")
        # Find the audio media enclosure link if available
        for link in entry.get("links", []):
            if "audio" in link.get("type", ""):
                episode.size = link['length']
                episode.link = link['href']
                # You should also try to determine file size and length if possible

        episode.save()
    generate_external_rss_feed_rss_file(rss_podcast_feed)