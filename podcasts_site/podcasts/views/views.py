from django.http import HttpResponse
from django.template import loader

from podcasts.models import YouTubePodcast


# Create your views here.
def index(request):
    if request.POST.get("action", False) == "Create":
        substring = request.POST['title_substring'].strip(),
        country_code = request.POST['country_code'].strip()
        YouTubePodcast(
            url = request.POST['url'], index_range=request.POST['index_range'],
            title_substring=None if len(substring) == 0 else substring, when_to_pull=request.POST['when_to_pull'],
            country_code = 'US' if len(country_code) == 0 else country_code
        ).save()
    elif request.POST.get("action", False) == "Update":
        podcast = YouTubePodcast.objects.all().filter(id=int(request.POST['id'])).first()
        if podcast:
            title_substring = request.POST['title_substring'].strip()
            country_code = request.POST['country_code'].strip()
            podcast.url = request.POST['url']
            podcast.title_substring = None if len(title_substring) == 0 else title_substring
            podcast.country_code = 'US' if len(country_code) == 0 else country_code
            podcast.range = request.POST['range']
            podcast.when_to_pull = request.POST['when_to_pull']
            podcast.save()
    template = loader.get_template("podcasts/index.html")
    context = {
        "podcasts" : YouTubePodcast.objects.all().filter(being_processed=False)
    }
    return HttpResponse(template.render(context, request))