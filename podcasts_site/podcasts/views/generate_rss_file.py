import datetime

from django.db.models import Q
from podgen import Category, Podcast, Person, Episode, Media

from podcasts.models import YouTubePodcast


def generate_rss_file(youtube_podcast: YouTubePodcast):
    category = None
    subcategory = None
    try:
        if youtube_podcast.category == 'News & Politics':
            category = 'News'
            subcategory = 'Politics'
        else:
            category = youtube_podcast.category
        category = Category(category=category, subcategory=subcategory)
    except ValueError:
        pass
    except TypeError:
        return
    videos = youtube_podcast.youtubevideo_set.all()
    p = Podcast(
        name=youtube_podcast.frontend_name,
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
            for video in videos.exclude(Q(hide=True) | Q(manually_hide=True))
        ]
    )
    p.rss_file(youtube_podcast.feed_file_location)
    print(f"done with {youtube_podcast.name}")