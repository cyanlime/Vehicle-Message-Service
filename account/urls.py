from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^vehicle_sign_in/$', views.vehicle_sign_in),
    url(r'^show_bind_qrcode/$', views.show_bind_qrcode),
    url(r'^wechat_events/$', views.WeChatEventsView.as_view()),
]
