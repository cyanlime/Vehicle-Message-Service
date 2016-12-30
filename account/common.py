""" Expose Common Methods
"""

import json
import datetime
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from .utils import decode_token
from .models import Vehicle

### views methods

def fetch_token(request):
    return request.META.get('HTTP_AUTHORIZATION', None)

def render_bad_request_response(self, errcode=100, errmsg='Bad Request'):
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

def wechat_authenticate(request):
    """ Through Web OAuth mechanism fetch wechat user info
    """
    code = request.GET.get('code', None)