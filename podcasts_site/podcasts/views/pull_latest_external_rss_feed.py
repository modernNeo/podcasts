import datetime
import re

import dateparser
import feedparser
import requests

from podcasts.models import RSSPodcastFeed, RssPodcastEpisode
from podcasts.views.generate_rss_file import generate_external_rss_feed_rss_file


def pull_latest_external_rss_feed(rss_podcast_feed: RSSPodcastFeed):
    # Provide a standard browser User-Agent to prevent the server from blocking the request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(rss_podcast_feed.url, headers=headers)
    response.raise_for_status()  # Throws an exception if the request failed
    parsed_feed = feedparser.parse(response.text)

    # 2. Initialize your podgen Podcast object
    rss_podcast_feed.name = parsed_feed.feed.get("title", "Unknown")
    rss_podcast_feed.description = parsed_feed.feed.get("subtitle", "Converted feed")
    rss_podcast_feed.language = "en"
    rss_podcast_feed.owner_email = parsed_feed['feed']['authors'][0]['email']
    rss_podcast_feed.owner_name = parsed_feed['feed']['authors'][0]['name']
    rss_podcast_feed.save()

    entries_dict = [episode.video_id for episode in rss_podcast_feed.rsspodcastepisode_set.all()]

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
        duration = entry['itunes_duration']
        if re.match(r"\d\d:\d\d:\d\d", duration):
            hours, minutes, seconds = duration.split(":")
            hours = int(hours)
            minutes = int(minutes)
            seconds = int(seconds)
            minutes += (hours * 60)
            episode.duration = int((minutes * 60) + seconds)
        else:
            episode.duration = int(duration)
        try:
            episode.date = datetime.datetime.strptime(entry.get("published"), "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            episode.date = dateparser.parse(entry.get("published"), settings={"RETURN_AS_TIMEZONE_AWARE": True})
            # Find the audio media enclosure link if available
        for link in entry.get("links", []):
            if "audio" in link.get("type", ""):
                episode.size = get_size(int(link['length']), link['href'])
                episode.link = link['href']
                # You should also try to determine file size and length if possible

        episode.save()
    generate_external_rss_feed_rss_file(rss_podcast_feed)


def get_size(length, audio_url):
    if length > 0:
        return length
    try:
        # Send a HEAD request.
        # allow_redirects=True is crucial here because of the Spotify/Podtrac tracking prefixes!
        response = requests.head(audio_url, allow_redirects=True, timeout=10)

        # Check for the Content-Length header
        content_length = response.headers.get("Content-Length")

        if content_length:
            file_size_bytes = int(content_length)
            print(f"Actual file size: {file_size_bytes:,} bytes")
            # Optional: Convert to MB for readability
            print(f"Approx size: {file_size_bytes / (1024 * 1024):.2f} MB")
            return file_size_bytes
        else:
            print("Server did not provide a Content-Length header.")

    except requests.RequestException as e:
        print(f"Could not fetch headers: {e}")