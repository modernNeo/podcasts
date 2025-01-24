from podcasts.models import YouTubePodcast
from podcasts.views.pstdatetimefield import pstdatetime


def update_podcast_being_processed(podcast_being_processed : YouTubePodcast, timestamp: pstdatetime, information, thumbnail):
    if podcast_being_processed.information_last_updated is None or timestamp > podcast_being_processed.information_last_updated:
        podcast_being_processed.name = information['playlist'].replace("?", "")
        if len(information['description']) > 0:
            podcast_being_processed.description = information['description']
        podcast_being_processed.image = thumbnail
        podcast_being_processed.language = "en-US"
        podcast_being_processed.author = information['uploader']
        podcast_being_processed.category = information['categories'][0]
        podcast_being_processed.information_last_updated = timestamp
        podcast_being_processed.save()
