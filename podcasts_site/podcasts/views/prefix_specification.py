from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

from podcasts.models import YouTubePodcast, YouTubePodcastTitlePrefix


def index(request, podcast_id):
    youtube_podcast = YouTubePodcast.objects.all().filter(id=podcast_id).first()
    if not youtube_podcast:
        return HttpResponseRedirect("/")
    if request.POST.get("action", False) == "Create":
        title_prefix = request.POST['title_prefix'].strip()
        priority = request.POST['priority'].strip()
        YouTubePodcastTitlePrefix(
            title_prefix=title_prefix,
            priority=priority,
            podcast=youtube_podcast
        ).save()
    elif request.POST.get("action", False) == "Update":
        prefix = YouTubePodcastTitlePrefix.objects.all().filter(id=int(request.POST['id'])).first()
        if prefix:
            prefix.title_prefix = request.POST['title_prefix'].strip()
            prefix.priority = request.POST['priority'].strip()
            prefix.save()
    elif request.POST.get("action", False) == "Delete":
        prefix = YouTubePodcastTitlePrefix.objects.all().filter(id=int(request.POST['id'])).first()
        if prefix:
            prefix.delete()
    template = loader.get_template("podcasts/prefix_specification.html")
    context = {
        "youtube_podcast" : youtube_podcast,
        "prefixes" : youtube_podcast.youtubepodcasttitleprefix_set.all().order_by('priority')
    }
    return HttpResponse(template.render(context, request))