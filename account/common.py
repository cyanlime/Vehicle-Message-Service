""" Expose Common Methods
"""

import json, datetime
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from . import wechat
from . import settings
from .utils import encode_token, decode_token
from .models import Vehicle, WeChat

### views methods

def fetch_token(request):
    return request.META.get('HTTP_AUTHORIZATION', None)

def render_bad_request_response(errcode=100, errmsg='Bad Request'):
    json_context = json.dumps({
        'errcode': errcode,
        'errmsg': errmsg
    })
    return HttpResponse(
        json_context, content_type='application/json'
    )

### model methods

def get_vehicle_by_id(id):
    try:
        return Vehicle.objects.get(pk=id)
    except ObjectDoesNotExist:
        return None

def get_wechat_by_id(id):
    try:
        return WeChat.objects.get(pk=id)
    except ObjectDoesNotExist:
        return None

### auth methods

def vehicle_token_authenticate(token):
    """ Decode token and return vehicle id
    """
    (payload, err) = decode_token(token)
    if err is not None:
        return (None, err)
    type_ = payload.get('type', None)
    if type_ is None or type_ <> 'vehicle':
        return (None, 'Invalid credentials type')
    id = payload.get('user_id', -1)
    return (id, None)

def wechat_token_authenticate(token):
    """ Decode token and return wechat id
    """
    (payload, err) = decode_token(token)
    if err is not None:
        return (None, err)
    type_ = payload.get('type', None)
    if type_ is None or type_ <> 'wechat':
        return (None, 'Invalid credentials type')
    id = payload.get('user_id', -1)
    return (id, None)

def wechat_authenticate(code):
    """ Through Web OAuth mechanism fetch openid and return WeChat user token
    """
    ((web_access_token, openid), err) = wechat.fetch_web_access_token(
        settings.APP_ID, settings.APP_SECRET, code)
    if err is not None:
        return (None, err)
    try:
        instance = WeChat.objects.get(openid=openid)
    except ObjectDoesNotExist:
        return (None, 'WeChat user not found')
    token = encode_token(instance.id, 'wechat')
    return (token, None)

