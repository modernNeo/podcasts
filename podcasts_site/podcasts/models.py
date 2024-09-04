from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint, Q

from podcasts.views import pstdatetimefield

# Create your models here.

VIDEOS_FOLDER_NAME = "videos"
ARCHIVE_FOLDER_NAME = "archives"
RSS_FEED_FOLDER_NAME = 'rss_feed'

class CronSchedule(models.Model):
    hour = models.IntegerField()
    minute = models.IntegerField()

    def __str__(self):
        return f"scheduler for {self.hour} hour and {self.minute} minutes"

class YouTubePodcast(models.Model):
    # class Meta:
    #     constraints = [
    #         UniqueConstraint(name="one_process_in_progress", fields=['being_processed'], condition=Q(being_processed=True))
    #     ]

    name = models.CharField(max_length=1000)
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

    @property
    def front_end_when_to_pull(self):
        return self.when_to_pull.strftime("%H:%M:%S")

    @property
    def friendly_name(self):
        return self.name.replace(':', '').replace(' ', '_').replace(',', '').replace('.', '')

    @property
    def video_file_location(self):
        return f"{settings.MEDIA_ROOT}/{VIDEOS_FOLDER_NAME}/{self.friendly_name}"

    @property
    def archive_file_location(self):
        return f"{settings.MEDIA_ROOT}/{ARCHIVE_FOLDER_NAME}/{self.friendly_name}"

    @property
    def feed_file_location(self):
        return f"{settings.MEDIA_ROOT}/{RSS_FEED_FOLDER_NAME}/{self.friendly_name}.xml"

    @property
    def http_feed_location(self):
        return f"{settings.HTTP_AND_FQDN}{settings.MEDIA_URL}{RSS_FEED_FOLDER_NAME}/{self.friendly_name}.xml"

    def __str__(self):
        return self.name

class YouTubePodcastTitleSubString(models.Model):
    class Meta:
        constraints = [
            UniqueConstraint(fields=['podcast', 'priority'], name='unique_podcast_title_substring_priority')
        ]

    title_substring = models.CharField(max_length=1000, default=None, null=True)
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)

    priority = models.IntegerField(
        default=None
    )

    def __str__(self):
        return f"{self.podcast.name} substring {self.title_substring}"


class YouTubePodcastVideo(models.Model):
    class Meta:
        constraints = [
            UniqueConstraint(fields=['podcast', 'original_title'], name='unique_title'),
            UniqueConstraint(fields=['podcast', 'identifier_number'], name='unique_date_and_time')
        ]
    video_id = models.CharField(max_length=1000)
    filename = models.CharField(max_length=1000)
    original_title = models.CharField(max_length=1000)
    description = models.CharField(max_length=5000)
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
    date = pstdatetimefield.PSTDateTimeField()
    identifier_number = models.PositiveBigIntegerField()
    grouping_number = models.IntegerField()
    url = models.CharField(max_length=10000)
    extension = models.CharField(max_length=100)
    image = models.CharField(max_length=10000, null=True)
    size = models.PositiveBigIntegerField()
    hide = models.BooleanField(default=False)
    duration = models.PositiveBigIntegerField()

    @property
    def get_location(self):
        return f"{settings.HTTP_AND_FQDN}{settings.MEDIA_URL}{VIDEOS_FOLDER_NAME}/{self.podcast.friendly_name}/{self.filename}"

    def __str__(self):
        return f"{self.date} {self.podcast}: {self.filename}"



class YouTubePodcastVideoGrouping(models.Model):
    grouping_number = models.IntegerField()
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
    podcast_video = models.ForeignKey(YouTubePodcastVideo, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.grouping_number} grouping for {self.podcast.name}"


class YouTubeDLPError(models.Model):
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
    message = models.CharField(
        max_length=5000
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

    def __str__(self):
        return f"Error in file {self.error_file_path}"
