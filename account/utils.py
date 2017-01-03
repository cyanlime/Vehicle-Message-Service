""" Tool Methods
"""

import os, datetime, urlparse, jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
from django.conf import settings as django_settings
from . import settings
from . import wechat
from .models import Vehicle, Article

def encode_token(id, type_):
    payload = {
        'user_id': id,
        'type': type_,
        'exp': datetime.datetime.utcnow() + settings.JWT_EXPIRATION_DELTA
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
        return instance.pk
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