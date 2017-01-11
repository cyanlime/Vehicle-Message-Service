from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^sync_points/$', views.sync_points),
    url(r'^current_point/$', views.current_point),
    url(r'^series_point/$', views.series_point)
]