import datetime

from django.db.models import Q
from podgen import Category, Podcast, Person, Episode, Media

from podcasts.models import YouTubePodcast, CustomList, RSSPodcastFeed


def generate_rss_file(youtube_podcast: YouTubePodcast):
    subcategory = None
    try:
        if youtube_podcast.category == 'News & Politics':
            category = 'News'
            subcategory = 'Politics'
        else:
            category = youtube_podcast.category
        category = Category(category=category, subcategory=subcategory)
    except ValueError:
        category = None
    except TypeError:
        return
    videos = youtube_podcast.youtubevideo_set.all().exclude(Q(hide=True) | Q(manually_hide=True)).order_by('-date')
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
                id=video.video_id if youtube_podcast.youtube_id else f"{video.date}-{video.get_title}",
                title=video.get_title,
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
            for video in videos
        ]
    )
    p.rss_file(youtube_podcast.feed_file_location)
    print(f"done with {youtube_podcast.name}")


def generate_custom_list_rss_file(custom_list_id):
    custom_list = CustomList.objects.all().filter(id=custom_list_id).first()
    episodes = []
    for podcast in custom_list.customlistentry_set.all():
        youtube_podcast = podcast.podcast
        if youtube_podcast:
            videos = youtube_podcast.youtubevideo_set.all().exclude(Q(hide=True) | Q(manually_hide=True))
            episodes.extend([
                Episode(
                    id=video.video_id if youtube_podcast.youtube_id else f"{video.date}-{video.get_title}",
                    title=video.get_title,
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
                for video in videos
            ])
        else:
            person = Person(name=podcast.external_podcast.owner_name, email=podcast.external_podcast.owner_email)
            episodes.extend([
                Episode(
                    id=ep.video_id,
                    title=ep.original_title,
                    summary=ep.description,
                    authors=[person],
                    image=ep.image,
                    media=Media(
                        duration=datetime.timedelta(seconds=ep.duration),
                        size=ep.size,
                        url=ep.link
                    ),
                    publication_date=ep.date,
                )
                for ep in podcast.external_podcast.rsspodcastepisode_set.all()
            ])
    episodes.sort(key=lambda x: x.publication_date, reverse=True)
    p = Podcast(
        name=custom_list.name,
        # owner=Person(youtube_podcast.author), commenting out cause it needs an email
        explicit=False,
        website="https://podcasts.modernneo.com/",
        description=custom_list.name,
        episodes=episodes
    )
    p.rss_file(custom_list.feed_file_location)
    print(f"done with {custom_list.name}")


def generate_external_rss_feed_rss_file(rss_podcast_feed: RSSPodcastFeed):
    my_podcast = Podcast()
    my_podcast.name = rss_podcast_feed.name
    my_podcast.description = rss_podcast_feed.description
    my_podcast.website = rss_podcast_feed.url
    my_podcast.language = "en"
    person = Person(name=rss_podcast_feed.owner_name, email=rss_podcast_feed.owner_email)
    my_podcast.authors = [person]
    my_podcast.owner = person
    my_podcast.explicit = False

    # 3. Iterate through the external entries and add them as episodes
    for entry in rss_podcast_feed.rsspodcastepisode_set.all():
        episode = Episode()
        episode.id = entry.video_id
        episode.title = entry.original_title
        episode.summary = entry.description
        episode.authors = [person]
        last_index = entry.image.rfind(".")
        if entry.image[last_index:] not in [".jpg", ".jpeg", ".png"]:
            episode.image = entry.image.split("?")[0]
        else:
            episode.image = entry.image
        episode.publication_date = entry.date
        episode.media = Media(
            duration=datetime.timedelta(seconds=entry.duration),
            size=entry.size,
            url=entry.link
        )
        my_podcast.add_episode(episode)
    my_podcast.rss_file(rss_podcast_feed.feed_file_location)
    print(f"done with {my_podcast.name}")