from django.http import HttpResponse
from django.template import loader

from podcasts.models import YouTubePodcast


# Create your views here.
def index(request):
    if request.POST.get("action", False) == "Create":
        substring = request.POST['title_substring'].strip()
        YouTubePodcast(
            url = request.POST['url'], index_range=request.POST['index_range'],
            title_substring=None if len(substring) == 0 else substring, when_to_pull=request.POST['when_to_pull']
        ).save()
    elif request.POST.get("action", False) == "Update":
        podcast = YouTubePodcast.objects.all().filter(id=int(request.POST['id'])).first()
        if podcast:
            description = request.POST['description'].strip()
            podcast.url = request.POST['url']
            podcast.title_substring = request.POST['title_substring']
            podcast.range = request.POST['range']
            podcast.when_to_pull = request.POST['when_to_pull']
            podcast.description = None if len(description) == 0 else description
            podcast.save()
    template = loader.get_template("podcasts/index.html")
    context = {
        "podcasts" : YouTubePodcast.objects.all().filter(being_processed=False)
    }
    return HttpResponse(template.render(context, request))