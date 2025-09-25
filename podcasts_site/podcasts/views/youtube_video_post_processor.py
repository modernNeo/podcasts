import os

from yt_dlp import postprocessor

from podcasts.models import YouTubePodcast, PodcastVideoGrouping, string_cleaner, YouTubeVideo
from podcasts.views.get_thumbnails import get_thumbnails
from podcasts.views.setup_logger import Loggers
from podcasts.views.timestamps.get_timestamp import get_timestamp
from podcasts.views.update_podcast_being_processed import update_podcast_being_processed


class YouTubeVideoPostProcessor(postprocessor.common.PostProcessor):
    def __init__(self):
        super(YouTubeVideoPostProcessor, self).__init__(None)

    def run(self, information):
        youtube_dlp_logger = Loggers.get_logger("youtube_dlp")
        full_path = information['filename']
        if os.path.exists(full_path):
            youtube_dlp_logger.info("###############################################")
            youtube_dlp_logger.info(f"# Starting Post-Processing video {full_path} #")
            youtube_dlp_logger.info("###############################################")
            slash_indices = [index for index, character in enumerate(full_path) if character == "/"]
            number_of_slashes = len(slash_indices)
            podcast_being_processed = YouTubePodcast.objects.all().filter(being_processed=True).first()
            if podcast_being_processed:
                youtube_id = information['id']
                current_file_name = full_path[slash_indices[number_of_slashes - 1] + 1:]
                youtube_dlp_logger.info(
                    f"[youtube_video_post_processor.py run()] current_file_name={current_file_name}")
                timestamp, cbc_vancouver_news_video = get_timestamp(information, current_file_name,
                                                                    podcast_being_processed)
                if timestamp:
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] podcast_being_processed.information_last_updated="
                        f"{podcast_being_processed.information_last_updated}"
                    )
                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] timestamp={timestamp}")
                    thumbnail = get_thumbnails(information)
                    update_podcast_being_processed(podcast_being_processed, timestamp, information, thumbnail)

                    new_file_name = f"{timestamp.strftime('%Y-%m-%d-%H-%M')}-{current_file_name}"
                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] new_file_name={new_file_name}")

                    index_of_last_period = new_file_name.rfind('.')
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] index_of_last_period={index_of_last_period}")
                    if index_of_last_period != -1:
                        youtube_dlp_logger.info(
                            f"[youtube_video_post_processor.py run()] new_file_name[index_of_last_period:]="
                            f"{new_file_name[index_of_last_period:]}"
                        )

                        if podcast_being_processed.cbc_news:
                            new_file_name = (
                                f"{new_file_name[:index_of_last_period]}_{youtube_id}"
                                f"{new_file_name[index_of_last_period:]}"
                            )
                            youtube_dlp_logger.info(
                                f"[youtube_video_post_processor.py run()] new_file_name for cbc_news={new_file_name}"
                            )

                    new_file_name = string_cleaner(new_file_name)
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] cleaned new_file_name={new_file_name}"
                    )
                    old_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{current_file_name}"
                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] old_file_path={old_file_path}")
                    new_file_path = f"{full_path[:slash_indices[number_of_slashes - 1] + 1]}{new_file_name}"

                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] new_file_path={new_file_path}")

                    os.rename(old_file_path, new_file_path)
                    release_stamp = int(timestamp.strftime('%Y-%m-%d-%H-%M').replace("-", ""))
                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] release_stamp={release_stamp}")
                    grouping_release_stamp = int(timestamp.strftime('%Y-%m-%d').replace("-", ""))
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] grouping_release_stamp={grouping_release_stamp}")

                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] information[title]={information.get('title', None)}")
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] information[description]={information.get('description', None)}")
                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] podcast={podcast_being_processed}")
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] information[original_url]={information.get('original_url', None)}")
                    youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] information[thumbnail]={thumbnail}")
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] information[filesize]={information.get('filesize', None)}")
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] information[filesize_approx]={information.get('filesize_approx', None)}")
                    youtube_dlp_logger.info(
                        f"[youtube_video_post_processor.py run()] information[duration]={information.get('duration', None)}")
                    file_size = information.get('filesize', None)
                    if not file_size:
                        file_size = information.get('filesize_approx', None)
                    if file_size is None:
                        youtube_dlp_logger.error(f"could not find the file size for {information['title']}")
                    else:
                        youtube_podcast_video = YouTubeVideo.objects.all().filter(
                            video_id=youtube_id).first()
                        if not youtube_podcast_video:
                            youtube_podcast_video = YouTubeVideo()
                        youtube_podcast_video.file_not_found = False
                        youtube_podcast_video.video_id = youtube_id
                        youtube_podcast_video.filename = new_file_name
                        youtube_podcast_video.original_title = information['title']
                        youtube_podcast_video.description = information["description"]
                        youtube_podcast_video.podcast = podcast_being_processed
                        youtube_podcast_video.date = timestamp
                        youtube_podcast_video.identifier_number = release_stamp
                        youtube_podcast_video.grouping_number = grouping_release_stamp
                        youtube_podcast_video.url = information['original_url']
                        youtube_podcast_video.image = thumbnail
                        youtube_podcast_video.size = file_size
                        youtube_podcast_video.extension = new_file_name[index_of_last_period:]
                        youtube_podcast_video.duration = information['duration']
                        youtube_podcast_video.save()
                        youtube_dlp_logger.info(f"[youtube_video_post_processor.py run()] {youtube_podcast_video} saved")
                        if cbc_vancouver_news_video:
                            youtube_podcast_video_grouping = PodcastVideoGrouping(
                                grouping_number=grouping_release_stamp, podcast=podcast_being_processed,
                                podcast_video=youtube_podcast_video
                            )
                            youtube_podcast_video_grouping.save()
                            youtube_dlp_logger.info(
                                f"[youtube_video_post_processor.py run()] {youtube_podcast_video_grouping} saved")
            youtube_dlp_logger.info("###############################################")
            youtube_dlp_logger.info(f"# Finished Post-Processing video {full_path} #")
            youtube_dlp_logger.info("###############################################")
        else:
            youtube_dlp_logger.error("##############################################")
            youtube_dlp_logger.error(f"# Unable to Post-Process video {full_path}  #")
            youtube_dlp_logger.error("##############################################")
        return [], information
