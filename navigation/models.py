from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Point(models.Model):
    vehicle = models.ForeignKey('account.Vehicle', on_delete=models.CASCADE)
    longitude = models.CharField(max_length=200, null=False, blank=False)
    latitude = models.CharField(max_length=200, null=False, blank=False)
    bearing = models.CharField(max_length=200)
    speed = models.CharField(max_length=200)
    time = models.DateTimeField(null=False)
    def __unicode__(self):
        return unicode(self.vehicle.vin)