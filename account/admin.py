from django.contrib import admin

from .models import *

# Register your models here.

class VehicleAdmin(admin.ModelAdmin):
    #list_display = ('id', 'create_time')
    list_display = ('id', 'create_time', 'vin', 'code')
    search_fields = ['vin']

class WeChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'openid', 'vehicle', 'bind', 'info', 'syntime')
    search_fields = ['openid']

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'key', 'title', 'desc', 'image', 'url')
    search_fields = ['title']

admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(WeChat, WeChatAdmin)
admin.site.register(Article, ArticleAdmin)