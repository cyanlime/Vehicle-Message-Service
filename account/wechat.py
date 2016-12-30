""" WeChat Helper
"""

from urllib import quote_plus
import datetime, json
import requests

wechat_access_token_url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=' \
    'client_credential&appid=%s&secret=%s'
wechat_qrcode_url = 'https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token=%s'
wechat_qrcode_show_url = 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=%s'

cache_access_token = None

class Expirable(object):
    def __init__(self, val, expire_time):
        self.value = val
        self.expire_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=expire_time)

    def val(self):
        return self.value

    def is_expired(self):
        return self.expire_time < datetime.datetime.utcnow()

def fetch_access_token(appid, appsecret):
    """ Through AppID and AppSecret fetch access token
    """
    global cache_access_token
    if cache_access_token is None or cache_access_token.is_expired():
        request_url = wechat_access_token_url % (appid, appsecret)
        try:
            resp = requests.get(request_url)
        except requests.RequestException:
            return (None, 'Failed to connect to WeChat server')
        try:
            request_json = resp.json()
        except ValueError:
            return (None, 'Unable to parse the response data from WeChat server')
        errcode = request_json.get('errcode', None)
        if errcode is not None:
            errmsg = request_json.get('errmsg', 'Unknown Error')
            return (None, errmsg)
        access_token = request_json.get('access_token', None)
        expires_in = request_json.get('expires_in', 7200)
        if access_token is None:
            return (None, 'Unknown Error')
        cache_access_token = Expirable(access_token, expires_in)
    return (cache_access_token.val(), None)

def generate_temp_qrcode(access_token, scene_id):
    """ Through access_token and scene_id generate QRCode 
    """
    global cache_access_token
    json_context = {
        'expire_seconds': 259200,
        'action_name': 'QR_SCENE',
        'action_info': {
            'scene': {
                'scene_id': scene_id
            }
        }
    }
    json_context = json.dumps(json_context)
    request_url = wechat_qrcode_url % access_token
    try:
        resp = requests.post(request_url, data=json_context)
    except requests.RequestException:
        return (None, 'Failed to connect to WeChat server')
    try:
        request_json = resp.json()
    except ValueError:
        return (None, 'Unable to parse the response data from WeChat server')
    errcode = request_json.get('errcode', None)
    if errcode is not None:
        errmsg = request_json.get('errmsg', 'Unknown Error')
        return (None, errmsg)
    ticket = request_json.get('ticket', None)
    if ticket is None:
        return (None, 'Unknown Error')
    ticket = quote_plus(ticket)
    request_url2 = wechat_qrcode_show_url % ticket
    try:
        resp2 = requests.get(request_url2, stream=True)
    except requests.RequestException:
        return (None, 'Failed to connect to WeChat server')
    return (resp2, None)