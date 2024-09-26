from django.urls import path

from podcasts.views import views, substring_specification, all_videos, prefix_specification

urlpatterns = [
    path('', views.index, name="index"),
    path('all', all_videos.index, name="index"),
    path('substrings/<int:podcast_id>', substring_specification.index, name='substrings'),
    path('prefixes/<int:podcast_id>', prefix_specification.index, name='prefixes')
]