from yt_dlp import postprocessor

from podcasts.models import YouTubePodcast, YouTubePodcastVideo
from podcasts.views.pstdatetimefield import pstdatetime


class YouTubeVideoPostProcessor(postprocessor.common.PostProcessor):
    def __init__(self):
        super(YouTubeVideoPostProcessor, self).__init__(None)

    def run(self, information):
        full_path = information['filename']
        slash_indices = [index for index, character in enumerate(full_path) if character == "/"]
        number_of_slashes = len(slash_indices)
        podcast = YouTubePodcast.objects.all().filter(being_processed=True).first()
        if podcast:
            podcast.name = information['playlist']
            podcast.description = information['description']
            podcast.image = information['thumbnail']
            podcast.language = "en-US"
            podcast.author = information['uploader']
            podcast.category = information['categories'][0]
            podcast.save()
            timestamp = pstdatetime.from_epoch(
                information['release_timestamp'] if information['release_timestamp'] else information['timestamp']
            )
            current_file_name = full_path[slash_indices[number_of_slashes - 1] + 1:]
            new_file_name = f"{timestamp.strftime('%Y-%m-%d')}-{current_file_name}"

            # I was renaming the file previously to give it the date as the prefix, but that messes with the download_archive flag
            old_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{current_file_name}"
            new_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{new_file_name}"
            # os.rename(old_file_path, new_file_path)

            YouTubePodcastVideo(
                filename=current_file_name, original_title=information['title'], description=information["description"],
                podcast=podcast, date=timestamp, number=int(timestamp.strftime('%Y-%m-%d').replace("-", "")),
                url=information['original_url'], image=information['thumbnail'], size=information['filesize'],
                extension=current_file_name[new_file_name.rfind("."):]
            ).save()
        return [], information
