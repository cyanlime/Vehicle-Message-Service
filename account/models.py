from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Vehicle(models.Model):
    vin = models.CharField(max_length=200, unique=True, null=False, blank=False)
    code = models.CharField(max_length=200, null=False, blank=False)

class WeChat(models.Model):
    openid = models.CharField(max_length=200, unique=True, null=False, blank=False)