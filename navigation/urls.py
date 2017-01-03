from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^sync/$', views.sync_points),
    url(r'^current_point/$', views.current_point),
]
