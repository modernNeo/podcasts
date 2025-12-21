import datetime
import logging
import os.path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import UniqueConstraint, Q

from podcasts.views import pstdatetimefield

# Create your models here.

VIDEOS_FOLDER_NAME = "videos"
ARCHIVE_FOLDER_NAME = "archives"
RSS_FEED_FOLDER_NAME = 'rss_feeds'
ARCHIVE_FOLDER_PATH = f"{settings.MEDIA_ROOT}/{ARCHIVE_FOLDER_NAME}"

class CronSchedule(models.Model):
    hour = models.IntegerField()
    minute = models.IntegerField()

    def __str__(self):
        return f"scheduler for {self.hour} hour and {self.minute} minutes"

def string_cleaner(name):
    return (name.replace(':', '').replace(' ', '_').replace(',', '').replace("/", "_")
            .replace("%", "").replace(";", "").replace("#", "").replace("?", ""))

class YouTubePodcast(models.Model):
    # class Meta:
    #     constraints = [
    #         UniqueConstraint(name="one_process_in_progress", fields=['being_processed'], condition=Q(being_processed=True))
    #     ]

    name = models.CharField(max_length=1000)
    custom_name = models.CharField(max_length=1000, null=True)
    description = models.CharField(max_length=5000)
    image = models.CharField(max_length=10000, null=True)
    language = models.CharField(max_length=5)
    author = models.CharField(max_length=10000)
    url = models.CharField(max_length=10000)
    when_to_pull = models.TimeField()
    being_processed = models.BooleanField(default=False)
    category = models.CharField(max_length=1000)
    index_range = models.IntegerField(null=True)
    information_last_updated = pstdatetimefield.PSTDateTimeField(
        null=True
    )
    cbc_news = models.BooleanField(default=False)


    @property
    def front_end_when_to_pull(self):
        return self.when_to_pull.strftime("%H:%M:%S")

    @property
    def frontend_name(self):
        return self.name if self.custom_name is None else self.custom_name

    @property
    def url_friendly_name(self):
        return string_cleaner(self.name) if self.custom_name is None else string_cleaner(self.custom_name)

    @property
    def video_file_location(self):
        return f"{settings.MEDIA_ROOT}/{VIDEOS_FOLDER_NAME}/{self.url_friendly_name}"

    @property
    def archive_file_location(self):
        return f"{settings.MEDIA_ROOT}/{ARCHIVE_FOLDER_NAME}/{self.url_friendly_name}"

    @property
    def feed_file_location(self):
        return f"{settings.MEDIA_ROOT}/{RSS_FEED_FOLDER_NAME}/{self.url_friendly_name}.xml"

    @property
    def http_feed_location(self):
        return f"{settings.HTTP_AND_FQDN}{settings.MEDIA_URL}{RSS_FEED_FOLDER_NAME}/{self.url_friendly_name}.xml"

    def get_videos(self):
        return list(self.youtubevideo_set.all())

    @property
    def shown_visible_videos_count(self):
        total = self.youtubevideo_set.all().exclude(
                Q(hide=True) | Q(manually_hide=True)
            ).count()
        return 3 if total >= 3 else total

    @property
    def all_videos_count(self):
        return self.youtubevideo_set.all().count()

    @property
    def front_end_get_visible_videos_list(self):
        return self.youtubevideo_set.all().exclude(
                Q(hide=True) | Q(manually_hide=True)
            ).order_by('-identifier_number')

    @property
    def front_end_get_all_videos_list(self):
        return self.youtubevideo_set.all().order_by('-identifier_number')


    def get_video_filenames(self):
        return list(self.youtubevideo_set.all().values_list('filename', flat=True))

    def __str__(self):
        return self.name if self.custom_name is None else self.custom_name

class YouTubePodcastTitleSubString(models.Model):
    class Meta:
        constraints = [
            UniqueConstraint(fields=['podcast', 'priority'], name='unique_podcast_title_substring_priority')
        ]

    title_substring = models.CharField(max_length=1000, default=None, null=True)
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
    priority = models.IntegerField(default=None)

    def __str__(self):
        return f"{self.podcast.frontend_name} substring {self.title_substring}"

# class YouTubePodcastTimestampPriority(models.Model):
#     class Meta:
#         constraints = [
#             UniqueConstraint(fields=['podcast', 'priority'], name='unique_podcast_timestamp_priority')
#         ]
#     timestamp = PSTDateTimeField()
#     podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
#     priority = models.IntegerField(default=None)
#
#     def __str__(self):
#         return f"{self.podcast.frontend_name} timestamp {self.timestamp}"

class YouTubePodcastTitlePrefix(models.Model):
    class Meta:
        constraints = [
            UniqueConstraint(fields=['podcast', 'priority'], name='unique_podcast_title_prefix_priority')
        ]

    title_prefix = models.CharField(max_length=1000, default=None, null=True)
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
    priority = models.IntegerField(default=None)

    def __str__(self):
        return f"{self.podcast.frontend_name} prefix {self.title_prefix}"

class YouTubeVideo(models.Model):

    video_id = models.CharField(max_length=1000, unique=True)
    filename = models.CharField(max_length=1000)
    original_title = models.CharField(max_length=1000)
    description = models.CharField(max_length=5000)
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
    date = pstdatetimefield.PSTDateTimeField()
    identifier_number = models.PositiveBigIntegerField()
    grouping_number = models.IntegerField()
    url = models.CharField(max_length=10000, unique=True)
    extension = models.CharField(max_length=100)
    image = models.CharField(max_length=10000, null=True)
    size = models.PositiveBigIntegerField()
    hide = models.BooleanField(default=False)
    manually_hide = models.BooleanField(default=False)
    duration = models.PositiveBigIntegerField()
    file_not_found = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        if self.is_present():
            fs = FileSystemStorage()
            fs.delete(self.get_file_location)
        with open(self.podcast.archive_file_location, 'w') as f:
            for video in self.podcast.get_videos():
                if video.video_id != self.video_id:
                    f.write(f"youtube {video.video_id}\n")
        super(YouTubeVideo, self).delete(*args, **kwargs)

    @property
    def get_location(self):
        return f"{settings.HTTP_AND_FQDN}{settings.MEDIA_URL}{VIDEOS_FOLDER_NAME}/{self.podcast.url_friendly_name}/{self.filename}"

    @property
    def get_file_location(self):
        return f'{self.podcast.video_file_location}/{self.filename}'

    @property
    def get_front_end_duration(self):
        return f"{datetime.timedelta(seconds=self.duration)}"

    def is_present(self):
        return os.path.exists(self.get_file_location)

    @property
    def front_end_name(self):
        return f'{self.date.pst.strftime("%a %Y-%b %d %I:%M %p %Z")} {self.get_front_end_duration} - {self.original_title}'

    def __str__(self):
        return f"{self.date.pst} {self.podcast}: {self.original_title}"

class PodcastVideoGrouping(models.Model):
    grouping_number = models.IntegerField()
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
    podcast_video = models.ForeignKey(YouTubeVideo, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.grouping_number} grouping for {self.podcast.frontend_name}"

class LoggingFilePath(models.Model):
    error_file_path = models.CharField(
        max_length=500,
        default=None,
        null=True
    )
    warn_file_path = models.CharField(
        max_length=500,
        default=None,
        null=True
    )
    debug_file_path = models.CharField(
        max_length=500,
        default=None,
        null=True
    )

class VideoWithNewDateFormat(models.Model):
    video_title = models.CharField(
        max_length=10000
    )
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)

    def __str__(self):
        return f"Error [{self.video_title}] in podcast {self.podcast}"

class YouTubeDLPWarnError(models.Model):
    message = models.CharField(
        max_length=10000
    )
    request = models.CharField(
        max_length=100000,
        default=None,
        null=True
    )
    fixed = models.BooleanField(
        default=False
    )
    processed = models.BooleanField(
        default=False
    )
    levelno = models.IntegerField(
        default=logging.WARNING
    )
    video_unavailable = models.BooleanField(
        null=True
    )
    video_id = models.CharField(
        max_length=100,
        default=None,
        null=True
    )
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)


    def __str__(self):
        return f"Error [{self.message}] in podcast {self.podcast}"
