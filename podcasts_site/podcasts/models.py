from django.db import models

# Create your models here.

class YouTubePodcast(models.Model):
    name = models.CharField(max_length=1000)
    video_substring = models.CharField(max_length=1000, default=None, null=True)
    url = models.CharField(max_length=10000, default=None, null=True)
    range = models.IntegerField(default=None, null=True)
    when_to_pull = models.TimeField()
    description = models.CharField(max_length=5000)

    @property
    def front_end_when_to_pull(self):
        return self.when_to_pull.strftime("%H:%M:%S")

    def get_description(self):
        return self.episode_set.all().order_by('-podcast__episode__number').first().description

    def __str__(self):
        return self.name

class Episode(models.Model):
    name = models.CharField(max_length=1000)
    description = models.CharField(max_length=5000)
    podcast = models.ForeignKey(YouTubePodcast, on_delete=models.CASCADE)
    date = models.DateTimeField(default=None)
    number = models.IntegerField(default=None, primary_key=True)
    url = models.CharField(max_length=10000, default=None, null=True)
    extension = models.CharField(max_length=100)
    image = models.ImageField()

    def get_location(self):
        return f"https://podcasts.modernneo.com/assets/video/{self.podcast.name}/{self.name}{self.extension}"

    def __str__(self):
        return f"{self.date} {self.podcast}: {self.name}"
