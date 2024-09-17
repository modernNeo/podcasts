import datetime

from django.db.models import Q
from podgen import Category, Podcast, Person, Episode, Media


def generate_rss_file(youtube_podcast):
    category = None
    try:
        category = Category(youtube_podcast.category)
    except ValueError:
        pass
    p = Podcast(
        name=youtube_podcast.name,
        description=youtube_podcast.description,
        image=youtube_podcast.image,
        website=youtube_podcast.url,
        language=youtube_podcast.language,
        authors=[Person(youtube_podcast.author)],
        category=category,
        # owner=Person(youtube_podcast.author), commenting out cause it needs an email
        explicit=False,
        episodes=[
            Episode(
                title=video.original_title,
                summary=video.description,
                authors=[Person(youtube_podcast.author)],
                image=video.image,
                media=Media(
                    duration=datetime.timedelta(seconds=video.duration),
                    size=video.size,
                    url=video.get_location
                ),
                publication_date=video.date,
            )
            for video in youtube_podcast.youtubepodcastvideo_set.all().exclude(Q(hide=True) | Q(manually_hide=True))
        ]
    )
    p.rss_file(youtube_podcast.feed_file_location)
    print(f"done with {youtube_podcast.name}")