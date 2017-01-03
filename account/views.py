import json, shutil
import xml.etree.cElementTree as ET
from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from jwt.exceptions import InvalidKeyError
from django.views.decorators.csrf import csrf_exempt
from .common import (
    fetch_token,
    render_bad_request_response,
    get_vehicle_by_id, 
    vehicle_token_authenticate,
    wechat_authenticate
    )
import wechat
from . import settings
from . import utils
from .models import Vehicle, WeChat

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
def wechat_sign_in(request):
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return render_bad_request_response(101, 'Incorrect json format')
    code = request_json.get('code', None)
    if code is None:
        return render_bad_request_response(201, 'Missing parameter code')
    (token, err) = wechat_authenticate(code)
    if err is not None:
        return render_bad_request_response(201, err)
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
        return render_bad_request_response(303, 'Register vehicle not found')
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
        encode_str = wechat.sha1_encode(settings.WECHAT_TOKEN, timestamp, nonce)
        if signature <> encode_str:
            return render_bad_request_response(-1, "Bad Request")
        return HttpResponse(echostr)

    def handle_bind(self, from_username, scene_id):
        instance, created = WeChat.objects.get_or_create(openid=from_username)
        try:
            vehicle = Vehicle.objects.get(pk=scene_id)
        except ObjectDoesNotExist:
            return render_bad_request_response(-1, "Register vehicle not found")
        instance.vehicle = vehicle
        instance.save()
        json_context = json.dumps({
            'ok': 1
        })
        return HttpResponse(
            json_context, content_type='application/json'
        )

    def handle_subscribe(self, from_username):
        instance, created = WeChat.objects.get_or_create(openid=from_username)
        json_context = json.dumps({
            'ok': 1
        })
        return HttpResponse(
            json_context, content_type='application/json'
        )

    def handle_click(self, from_username, to_username, event_key):
        if event_key == 'more':
            xml = wechat.create_complex_msg(from_username, to_username, utils.get_articles(event_key))
            if xml is not None:
                return HttpResponse(
                    xml, content_type='text/xml'
                )
        return HttpResponse('')

    def parse_xml(self, xml):
        xml_tree = ET.fromstring(xml)
        to_username_node = xml_tree.find('ToUserName')
        from_username_node = xml_tree.find('FromUserName')
        create_time_node = xml_tree.find('CreateTime')
        msg_type_node = xml_tree.find('MsgType')
        event_node = xml_tree.find('Event')
        event_key_node = xml_tree.find('EventKey')
        ticket_node = xml_tree.find('Ticket')
        if to_username_node is None or from_username_node is None \
            or create_time_node is None or msg_type_node is None \
            or event_node is None:
            return render_bad_request_response(-1, "Bad Request")
        to_username = to_username_node.text
        from_username = from_username_node.text
        create_time = create_time_node.text
        msg_type = msg_type_node.text
        event = event_node.text
        event_key = event_key_node.text if event_key_node is not None else ''
        ticket = ticket_node.text if ticket_node is not None else ''
        if event == 'subscribe':
            if event_key is not None and len(event_key) > 0:
                self.handle_bind(from_username, event_key[len('qrscene_'):])
            return self.handle_subscribe(from_username)
        elif event == 'SCAN':
            return self.handle_bind(from_username, event_key)
        elif event == 'CLICK':
            return self.handle_click(from_username, to_username, event_key)
        else:
            return render_bad_request_response(-1, "Unhandled Event")

    def post(self, request):
        nonce = request.GET.get('nonce', None)
        openid = request.GET.get('openid', None)
        timestamp = request.GET.get('timestamp', None)
        encrypt_type = request.GET.get('encrypt_type', None)
        signature = request.GET.get('signature', None)
        msg_signature = request.GET.get('msg_signature', None)
        incoming_xml = request.body
        if nonce is None or openid is None \
            or timestamp is None or encrypt_type is None \
            or signature is None or msg_signature is None:
            return render_bad_request_response(-1, "Bad Request")
        (xml, err) = wechat.decrypt_msg(incoming_xml, msg_signature, timestamp, 
            nonce, settings.APP_ID, settings.ENCODING_AES_KEY, 
            settings.WECHAT_TOKEN)
        if err is not None:
            return render_bad_request_response(-1, "Bad Request")
        return self.parse_xml(xml)
