from django.urls import path

from podcasts.views import views

urlpatterns = [
    path('', views.index, name="index")
]