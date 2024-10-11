from django.http import HttpResponse
from django.template import loader

from podcasts.views.showing_videos import showing_videos


# Create your views here.
def index(request):
    return HttpResponse(
        loader.get_template("podcasts/index.html")
        .render(
            showing_videos(request), request
        )
    )