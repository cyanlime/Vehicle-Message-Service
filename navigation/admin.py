from django.contrib import admin

from .models import *

# Register your models here.

class PointAdmin(admin.ModelAdmin):
    list_display = ('id', 'longitude', 'latitude', 'bearing', 'speed', 'time', 'vehicle')
    search_fields = ['id']

admin.site.register(Point, PointAdmin)