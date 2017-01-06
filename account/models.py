from __future__ import unicode_literals

from django.db import models
from datetime import datetime

# Create your models here.

class Vehicle(models.Model):
    create_time = models.DateTimeField(auto_now_add=True)
    vin = models.CharField(max_length=200, unique=True, null=False, blank=False)
    code = models.CharField(max_length=200, null=False, blank=False)
    def __unicode__(self):
        return unicode(self.vin)

class WeChat(models.Model):
    openid = models.CharField(max_length=200, unique=True, null=False, blank=False)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.SET_NULL, null=True, blank=False)
    bind = models.BooleanField(default=False)
    info = models.CharField(max_length=200, null=True, blank=True)
    syntime = models.DateTimeField(default=datetime.fromtimestamp(0))
    def __unicode__(self):
        return unicode(self.openid)

    class Meta:
        verbose_name = 'WeChat'


class Article(models.Model):
    key = models.CharField(max_length=200, null=False, blank=False)
    title = models.CharField(max_length=200, null=False, blank=False)
    desc = models.CharField(max_length=200, null=False, blank=False)
    image = models.ImageField(upload_to='articles', null=False)
    url = models.CharField(max_length=200, null=False, blank=False)
    def __unicode__(self):
        return unicode(self.title)
  