from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint, Q

from podcasts.views import pstdatetimefield

# Create your models here.

VIDEOS_FOLDER_NAME = "videos"
ARCHIVE_FOLDER_NAME = "archives"
RSS_FEED_FOLDER_NAME = 'rss_feed'

class YouTubePodcast(models.Model):
    class Meta:
        constraints = [
            UniqueConstraint(name="one_process_in_progress", fields=['being_processed'], condition=Q(being_processed=True))
        ]

    name = models.CharField(max_length=1000)
    description = models.CharField(max_length=5000)
    image = models.CharField(max_length=10000)
    language = models.CharField(max_length=5)
    author = models.CharField(max_length=10000)
    title_substring = models.CharField(max_length=1000, default=None, null=True)
    url = models.CharField(max_length=10000)
    when_to_pull = models.TimeField()
    being_processed = models.BooleanField(default=False)
    category = models.CharField(max_length=1000)
    index_range = models.IntegerField()
    country_code = models.CharField(max_length=5, default="US")

    @property
    def front_end_when_to_pull(self):
        return self.when_to_pull.strftime("%H:%M:%S")

    @property
    def front_end_title_substring(self):
        return self.title_substring if self.title_substring else ""

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

class YouTubePodcastVideo(models.Model):
    class Meta:
        constraints = [
            UniqueConstraint(fields=['podcast', 'original_title'], name='unique_title'),
            UniqueConstraint(fields=['podcast', 'number'], name='unique_number')
        ]

    filename = models.CharField(max_length=1000)
    original_title = models.CharField(max_length=1000)
    description = models.CharField(max_length=5000)
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
    date = pstdatetimefield.PSTDateTimeField()
    number = models.IntegerField()
    url = models.CharField(max_length=10000)
    extension = models.CharField(max_length=100)
    image = models.ImageField()
    size = models.IntegerField()

    @property
    def get_location(self):
        return f"{settings.HTTP_AND_FQDN}{settings.MEDIA_URL}{VIDEOS_FOLDER_NAME}/{self.podcast.friendly_name}/{self.filename}"

    def __str__(self):
        return f"{self.date} {self.podcast}: {self.filename}"


