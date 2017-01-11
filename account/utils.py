#!/usr/bin/env Python
# coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os, datetime, urlparse, jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
from django.conf import settings as django_settings
from . import settings
from .models import Vehicle, Article, WeChat
import datetime, time, json
import wechat
from django.http import HttpResponse, JsonResponse

""" Tool Methods
"""

def encode_token(id, type_):
    payload = {
        'user_id': id,
        'type': type_,
        'exp': datetime.datetime.now() + settings.JWT_EXPIRATION_DELTA
    }
    return jwt.encode(payload, django_settings.SECRET_KEY, algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, django_settings.SECRET_KEY, algorithm='HS256')
        return (payload, None)
    except DecodeError:
        return (None, 'Invalid token')
    except ExpiredSignatureError:
        return (None, 'Token has expired')

def vehicle_authenticate(credentials):
    """ Return vehicle id if passed, otherwise return None
    """
    vin = credentials.get('vin', None)
    if vin is None:
        return None
    code = credentials.get('code', None)
    if code is None:
        return None
    instance, created = Vehicle.objects.get_or_create(vin=vin, defaults={
        'code': code
    })
    if created or instance.code == code:
        instance_create_time = instance.create_time+datetime.timedelta(hours=8)
        timestamp_instance_createtime = time.mktime(instance_create_time.timetuple())
        return instance.pk, timestamp_instance_createtime
    return None

def get_articles(key):
    """ Fetch articles from database based on key
    """
    articles = Article.objects.filter(key=key)
    objs = []
    for article in articles:
        path = os.path.join(django_settings.MEDIA_URL, article.image.url)
        image_url = urlparse.urljoin(settings.HOSTNAME_WITH_SCHEMA, path)
        obj = wechat.Article(
            title=article.title, desc=article.desc, 
            image=image_url, url=article.url)
        objs.append(obj)
    return objs

def synwxuserinfo(vehicle_id):
    """ Synchronization WeChat user's info
    """
    binding_wxusers = []
    instances = WeChat.objects.filter(vehicle=vehicle_id).filter(bind=True)
    for instance in instances:
        instance_id = instance.id
        instance_openid = instance.openid
        instance_bind = instance.bind
        if instance.syntime+datetime.timedelta(days=7)<datetime.datetime.now() or len(instance.info)==0:
            (access_token, err) = wechat.fetch_access_token(settings.APP_ID, settings.APP_SECRET)     
            if err is not None:
                return render_bad_request_response(-1, "Bad Request")
            (userinfo, err) = wechat.fetch_userinfo(access_token, instance_openid)
            if err is not None:
                return render_bad_request_response(-1, "Bad Request")
            instance.info = json.dumps(userinfo)
            instance.syntime = datetime.datetime.now()
            instance.save()     
        instance_info = json.loads(instance.info)
        name = instance_info.get('nickname')
        head_portrait = instance_info.get('headimgurl')
        instance_syntime = instance.syntime
        timestamp_instance_syntime = time.mktime(instance_syntime.timetuple())
        binding_wxuser = {'wechatid': instance_id,
            'info': {'name': name, 'head_portrait': head_portrait}, 'syntime': timestamp_instance_syntime}
        binding_wxusers.append(binding_wxuser)       
    return binding_wxusers

# def now():
# 	return int(time.mktime(datetime.now().timetuple()))

# def nonceStr():
# 	return str(uuid.uuid1()).replace('-', '')

# def generateSHA1Sign(d):
#     """ Generate sha1 signature
#     """
#     l = d.items()
#     l = filter(lambda t: t[1] is not None and len(t[1].strip()) > 0, l)
#     l = map(lambda t: '%s=%s' % t, l)
#     l = sorted(l)
#     stringSignTemp = reduce(lambda _1, _2: '%s&%s' % (_1, _2), l)
#     stringSignTemp = stringSignTemp.encode('utf8')
#     sha1Sign = hashlib.sha1(stringSignTemp).hexdigest()
#     return sha1Sign
