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
        explicit=False,
        episodes=[
            Episode(
                title=episode.original_title,
                media=Media(episode.get_location, size=episode.size),
                publication_date=episode.date
            )
            for episode in youtube_podcast.youtubepodcastvideo_set.all().filter(hide=False)
        ]
    )
    p.rss_file(youtube_podcast.feed_file_location)
    print(f"done with {youtube_podcast.name}")