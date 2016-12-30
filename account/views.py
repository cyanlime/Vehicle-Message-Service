import json, shutil, hashlib
from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
from jwt.exceptions import InvalidKeyError
from django.views.decorators.csrf import csrf_exempt
from .common import (
    fetch_token,
    render_bad_request_response,
    get_vehicle_by_id, 
    vehicle_token_authenticate
    )
import wechat
from . import settings
from . import utils

# Create your views here.

def index(request):
    return HttpResponse("From ngrok!")

@csrf_exempt
@require_http_methods(["POST"])
def vehicle_sign_in(request):
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return render_bad_request_response(101, 'Incorrect json format')
    id = utils.vehicle_authenticate(request_json)
    if id is None:
        return render_bad_request_response(201, 'Invalid vehicle credentials')
    token = utils.encode_token(id, 'vehicle')
    json_context = json.dumps({
        'token': token
    })
    return HttpResponse(
        json_context, content_type='application/json'
    )

@csrf_exempt
@require_http_methods(["POST"])
def show_bind_qrcode(request):
    token = fetch_token(request)
    if token is None:
        return render_bad_request_response(301, 'Missing authorization header')
    (vehicle_id, err) = vehicle_token_authenticate(token)
    if err is not None:
        return render_bad_request_response(302, err)
    vehicle = get_vehicle_by_id(vehicle_id)
    if vehicle is None:
        return render_bad_request_response(303, 'Unknown vehicle')
    (access_token, err) = wechat.fetch_access_token(settings.APP_ID, settings.APP_SECRET)
    if err is not None:
        return render_bad_request_response(303, err)
    (qrcode, err) = wechat.generate_temp_qrcode(access_token, vehicle.pk)
    if err is not None:
        return render_bad_request_response(303, err)
    response = FileResponse(qrcode.raw)
    response['Content-Type'] = qrcode.headers['Content-Type']
    return response
    
class WeChatEventsView(View):
    
    http_method_names = ['get', 'post']

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(WeChatEventsView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        signature = request.GET.get('signature', None)
        timestamp = request.GET.get('timestamp', None)
        nonce = request.GET.get('nonce', None)
        echostr = request.GET.get('echostr', None)
        if signature is None or timestamp is None or nonce is None or echostr is None:
            return render_bad_request_response(-1, "Bad Request")
        
        tmp_arr = sorted([settings.WECHAT_TOKEN, timestamp, nonce])
        tmp_str = reduce(lambda _1, _2: '%s%s' % (_1, _2), tmp_arr)
        tmp_str = hashlib.sha1(tmp_str).hexdigest()
        if signature <> tmp_str:
            return render_bad_request_response(-1, "Bad Request")
        return HttpResponse(echostr)

    def post(self, request):
        a = request.body
        pass