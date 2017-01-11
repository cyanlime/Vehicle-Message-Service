#!/usr/bin/env Python
# coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import json, shutil
import xml.etree.cElementTree as ET
from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, FileResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from jwt.exceptions import InvalidKeyError
from django.views.decorators.csrf import csrf_exempt
from .common import (
    fetch_token,
    render_bad_request_response,
    get_vehicle_by_id,
    get_wechat_by_id,
    vehicle_token_authenticate,
    wechat_authenticate
    )
import wechat
from . import settings
from . import utils
from .models import Vehicle, WeChat
import datetime, time

# Create your views here.

def index(request):
    return HttpResponse("From ngrok!")

@csrf_exempt
@require_http_methods(["POST"])
def vehicle_sign_in(request):
    """ Vehicle Sign in Interface
    """
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return render_bad_request_response(101, 'Incorrect json format')
    if utils.vehicle_authenticate(request_json) is None:
        vehicle = {'code': 1, 'result': {'errmsg': "Incoming code Incorrect."}}
        return JsonResponse(vehicle)
    (id, timestamp_vehicle_createtime) = utils.vehicle_authenticate(request_json)
    if (id, timestamp_vehicle_createtime) is None:
        return render_bad_request_response(201, 'Invalid vehicle credentials')
    token = utils.encode_token(id, 'vehicle')
    json_context = json.dumps({
        'code': 0,
        'result': {
            'create_time': timestamp_vehicle_createtime,
            'vin': id,
            'token': token
        }
    })
    return HttpResponse(
        json_context, content_type='application/json'
    )

@csrf_exempt
@require_http_methods(["POST"])
def wechat_sign_in(request):
    """ WeChat Sign in Interface
    """
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
    """ Bind QRCode showing Interface
    """
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
    """ WeChat event Class
    """
    http_method_names = ['get', 'post']

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(WeChatEventsView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        """ Verify validity of Server Address
        """
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

    def handle_bind(self, from_username, to_username, scene_id, with_subscribe):
        """ Handle vehicle-wechat binding event
        """
        instance, created = WeChat.objects.get_or_create(openid=from_username)
        try:
            vehicle = Vehicle.objects.get(pk=scene_id)
        except ObjectDoesNotExist:
            return render_bad_request_response(-1, "Register vehicle not found")

        welcome_str = ''
        if with_subscribe:
            welcome_str = u'感谢您关注车友同行公众号！这里可以帮您把手机和车机绑定的一起哦。'\
                    u'\n点击远程控制可查看车机相关信息，查看车的位置、轨迹，发送目的地给车机。'\
                    u'\n流量卡可助您快速充值，实时了解流量使用情况。\n'
        if instance.bind is False:
            instance.vehicle = vehicle
            instance.bind = True
            instance.save()
            xml = wechat.create_text_msg(from_username, to_username,
                welcome_str + u'您已成功绑定车机%s，如需绑定新车机，'\
                    u'请先<a href="http://car.yijiayinong.com/remove_binding.html">解绑</a>。' % vehicle.vin)
        else:
            xml = wechat.create_text_msg(from_username, to_username,
                welcome_str + u'您已绑定车机%s，如需绑定新车机，'\
                    u'请先<a href="http://car.yijiayinong.com/remove_binding.html">解绑</a>。' % vehicle.vin)
        if xml is not None:
            return HttpResponse(
                xml, content_type='text/xml'
            )
        return HttpResponse('')
       
    def handle_subscribe(self, from_username, to_username):
        """ Handle WeChat Subscribe event
        """
        instance, created = WeChat.objects.get_or_create(openid=from_username)
        welcome_str = u'感谢您关注车友同行公众号！这里可以帮您把手机和车机绑定的一起哦。'\
                    u'\n点击远程控制可查看车机相关信息，查看车的位置、轨迹，发送目的地给车机。'\
                    u'\n流量卡可助您快速充值，实时了解流量使用情况。\n'
        if instance.bind==False:
            xml = wechat.create_text_msg(from_username, to_username, welcome_str+\
                    u'您当前尚未绑定设备哦，如需绑定，'\
                    u'请先<a href="http://car.yijiayinong.com/scanQrcode.html">扫一扫</a>，对准设备上的二维码即可！')
        else:
             xml = wechat.create_text_msg(from_username, to_username, welcome_str+\
                    u'您已绑定车机%s，如需绑定新车机，'\
                    u'请先<a href="http://car.yijiayinong.com/remove_binding.html">解绑</a>。' % instance.vehicle.vin)
        if xml is not None:
            return HttpResponse(
                xml, content_type='text/xml'
            )
        return HttpResponse('')

    def handle_click(self, from_username, to_username, event_key):
        """ Handle WeChat Click event
        """
        if event_key == 'more':
            xml = wechat.create_complex_msg(from_username, to_username, utils.get_articles(event_key))
        if event_key == 'devices':
            instance = WeChat.objects.get(openid=from_username)
            if instance.bind==False:
                xml = wechat.create_text_msg(from_username, to_username,
                    u'您当前尚未绑定设备哦，如需绑定，'\
                    u'点击<a href="http://car.yijiayinong.com/scanQrcode.html">扫一扫</a>，对准设备上的二维码即可！')
            else:
                xml = wechat.create_text_msg(from_username, to_username,
                    u'您绑定的车机号为：%s。如需绑定新车机，'\
                    u'请先<a href="http://car.yijiayinong.com/remove_binding.html">解绑</a>。' % instance.vehicle.vin)
        if xml is not None:
            return HttpResponse(
                xml, content_type='text/xml'
            )
        return HttpResponse('')

    def parse_xml(self, xml):
        """ Parse XML Date Package
        """
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
                return self.handle_bind(from_username, to_username, event_key[len('qrscene_'):], True)
            else:
                return self.handle_subscribe(from_username, to_username)
        elif event == 'SCAN':
            return self.handle_bind(from_username, to_username, event_key, False)
        elif event == 'CLICK':
            return self.handle_click(from_username, to_username, event_key)
        else:
            return render_bad_request_response(-1, "Unhandled Event")

    def post(self, request):
        """ Encrypt and Check Return echostr parameter content
        """
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

@csrf_exempt
@require_http_methods(["POST"])
def bound_vehicles(request):
    """ Show wxusers binding to a vehicle
    """
    token = fetch_token(request)
    if token is None:
        return render_bad_request_response(301, 'Missing authorization header')
    (vehicle_id, err) = vehicle_token_authenticate(token)
    if err is not None:
        return render_bad_request_response(302, err)
    vehicle = get_vehicle_by_id(vehicle_id)
    if vehicle is None:
        return render_bad_request_response(303, 'Register vehicle not found')

    vehicle_vin = vehicle.vin
    vehicle_create_time = vehicle.create_time
    timestamp_vehicle_create_time = time.mktime(vehicle_create_time.timetuple())

    binding_wxuser = utils.synwxuserinfo(vehicle_id)
    bundled_accounts = {'code': 0, 'result': {'vehicle_id': vehicle_id,
        'create_time': timestamp_vehicle_create_time, 'vin': vehicle_vin, 'WXUsers': binding_wxuser}}
    return JsonResponse(bundled_accounts)

@csrf_exempt
@require_http_methods(["POST"])
def remove_binding(request):
    """ Remove binding on vehicle
    """
    token = fetch_token(request)
    if token is None:
        return render_bad_request_response(301, 'Missing authorization header')
    (vehicle_id, err) = vehicle_token_authenticate(token)
    if err is not None:
        return render_bad_request_response(302, err)
    vehicle = get_vehicle_by_id(vehicle_id)
    if vehicle is None:
        return render_bad_request_response(303, 'Register vehicle not found')

    try:
        request_json = json.loads(request.body)
    except ValueError:
        return render_bad_request_response(101, 'Incorrect json format')
    wechat_id = request_json.get('wechat_id')
    if len(wechat_id)==0:
        unbinding_accounts = {'code': 1, 'result': {'errmsg': "Incoming parameter value wechat_id missing."}}
        return JsonResponse(unbinding_accounts)
    wechat = get_wechat_by_id(wechat_id)
    if wechat is None:
        return render_bad_request_response(303, 'Wechat user not found')
    if wechat.vehicle.id==vehicle_id and wechat.bind==True:
        wechat.bind = False
        wechat.save()
        unbinding_accounts = {'code': 0, 'result': {'msg': "Remove binding successfully."}}
        return JsonResponse(unbinding_accounts)
    else:
        unbinding_accounts = {'code': 1, 'result': {'errmsg': "WXUser doesn't bind to the vehicle."}}
        return JsonResponse(unbinding_accounts)

@csrf_exempt
@require_http_methods(["POST"])
def wxJSconfig(request):
    """ WeChat JSConfig Interface
    """
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return render_bad_request_response(101, 'Incorrect json format')
    URL = request_json.get('url', None)
    JSApiList = request_json.get('jsApiList', None)
    if URL is None or len(JSApiList)==0:
        return render_bad_request_response(101, 'Missing parameter url or jsApiList.')
    wxJSconfig = wechat.createWXConfig(URL, JSApiList, settings.APP_ID, settings.APP_SECRET)
    return JsonResponse(wxJSconfig)

@csrf_exempt
@require_http_methods(["POST"])
def web_remove_binding(request):
    """ Remove binding Interface, Web
    """
    token = fetch_token(request)
    if token is None:
        return render_bad_request_response(301, 'Missing authorization header')
    (wechat_id, err) = wechat_token_authenticate(token)
    if err is not None:
        return render_bad_request_response(302, err)
    wechat = get_wechat_by_id(wechat_id)
    if wechat.vehicle is None:
        return render_bad_request_response(201, 'No related vehicle found')
    if wechat.bind==True:
        wechat.bind = False
        wechat.save()
        unbinding_accounts = {'code': 0, 'result': {'msg': "Remove binding successfully."}}
        return JsonResponse(unbinding_accounts)
    else:
        unbinding_accounts = {'code': 1, 'result': {'errmsg': "WXUser doesn't bind to the vehicle."}}
        return JsonResponse(unbinding_accounts)
