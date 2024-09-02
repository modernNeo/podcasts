from django.urls import path

from podcasts.views import views, substring_specification, all_videos

urlpatterns = [
    path('', views.index, name="index"),
    path('all', all_videos.index, name="index"),
    path('substrings/<int:podcast_id>', substring_specification.index, name='podcast_id')
]