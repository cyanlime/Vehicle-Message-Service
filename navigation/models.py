from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Point(models.Model):
    vehicle = models.ForeignKey('account.Vehicle', on_delete=models.CASCADE)
    latitude = models.CharField(max_length=200, null=False, blank=False)
    longitude = models.CharField(max_length=200, null=False, blank=False)
    time = models.DateTimeField(null=False)