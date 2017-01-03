from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Vehicle)
admin.site.register(WeChat)
admin.site.register(Article)