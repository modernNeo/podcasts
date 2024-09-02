from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

from podcasts.models import YouTubePodcast, YouTubePodcastTitleSubString


def index(request, podcast_id):
    youtube_podcast = YouTubePodcast.objects.all().filter(id=podcast_id).first()
    if not youtube_podcast:
        return HttpResponseRedirect("/")
    if request.POST.get("action", False) == "Create":
        title_substring = request.POST['title_substring'].strip()
        priority = request.POST['priority'].strip()
        YouTubePodcastTitleSubString(
            title_substring=title_substring,
            priority=priority,
            podcast=youtube_podcast
        ).save()
    elif request.POST.get("action", False) == "Update":
        substring = YouTubePodcastTitleSubString.objects.all().filter(id=int(request.POST['id'])).first()
        if substring:
            substring.title_substring = request.POST['title_substring'].strip()
            substring.priority = request.POST['priority'].strip()
            substring.save()
    elif request.POST.get("action", False) == "Delete":
        substring = YouTubePodcastTitleSubString.objects.all().filter(id=int(request.POST['id'])).first()
        if substring:
            substring.delete()
    template = loader.get_template("podcasts/substring_specification.html")
    context = {
        "youtube_podcast" : youtube_podcast,
        "substrings" : youtube_podcast.youtubepodcasttitlesubstring_set.all().order_by('priority')
    }
    return HttpResponse(template.render(context, request))