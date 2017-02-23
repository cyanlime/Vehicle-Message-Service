""" WeChat Helper
"""

from urllib import quote_plus
import datetime, json, hashlib, base64, socket, struct
import requests
import xml.etree.cElementTree as ET
from Crypto.Cipher import AES
import uuid, time

wechat_access_token_url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=' \
    'client_credential&appid=%s&secret=%s'
wechat_userinfo_url = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token=%s&openid=%s&lang=zh_CN'
wechat_web_access_token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=' \
    '%s&secret=%s&code=%s&grant_type=authorization_code'
wechat_web_userinfo_url = 'https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%s&lang=zh_CN'
wechat_qrcode_url = 'https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token=%s'
wechat_qrcode_show_url = 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=%s'
wechat_menu_create_url = 'https://api.weixin.qq.com/cgi-bin/menu/create?access_token=%s'
wechat_redirect_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=' \
    '%s&redirect_uri=%s&response_type=code&scope=%s&state=%s#wechat_redirect'
wechat_fetch_jsapi_ticket_url = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?type=jsapi&access_token=%s'


cache_access_token = None

class Expirable(object):
    def __init__(self, val, expire_time):
        self.value = val
        self.expire_time = datetime.datetime.now() + datetime.timedelta(seconds=expire_time)

    def val(self):
        return self.value

    def is_expired(self):
        return self.expire_time < datetime.datetime.now()

def generate_redirect_uri(redirect_uri, appid, state, scope='snsapi_base'):
    """ Generate WeChat OAuth redirect uri
    """
    return wechat_redirect_url % (appid, redirect_uri, scope, state)

def fetch_web_access_token(appid, appsecret, code):
    """ Through oauth code fetch web access token
    """
    request_url = wechat_web_access_token_url % (appid, appsecret, code)
    try:
        resp = requests.get(request_url)
    except requests.RequestException:
        return ((None, None), 'Failed to connect to WeChat server')
    try:
        request_json = resp.json()
    except ValueError:
        return ((None, None), 'Unable to parse the response data from WeChat server')
    errcode = request_json.get('errcode', None)
    if errcode is not None:
        errmsg = request_json.get('errmsg', 'Unknown Error')
        return ((None, None), errmsg)
    access_token = request_json.get('access_token', None)
    expires_in = request_json.get('expires_in', 7200)
    openid = request_json.get('openid', None)
    if access_token is None:
        return ((None, None), 'Unknown Error')
    return ((access_token, openid), None)

def fetch_web_userinfo(access_token, openid):
    """ Through web access token fetch user info
    """
    request_url = wechat_web_userinfo_url % (web_access_token, openid)
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
    return (request_json, None)

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

def fetch_userinfo(access_token, openid):
    """ Through web access token fetch user info
    """
    request_url = wechat_userinfo_url % (access_token, openid)
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
    return (request_json, None)

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

def sha1_encode(*args):
    tmp_arr = sorted(args)
    tmp_str = reduce(lambda _1, _2: '%s%s' % (_1, _2), tmp_arr)
    return hashlib.sha1(tmp_str).hexdigest()

def decrypt_msg(incoming_xml, msg_signature, timestamp, nonce, appid, aes_key, token):
    """ Decrypt incoming message
    """
    try:
        xml_tree = ET.fromstring(incoming_xml)
        encrypt_node = xml_tree.find('Encrypt')
        to_username_node = xml_tree.find('ToUserName')
        if encrypt_node is None or to_username_node is None:
            return (None, 'Invalid xml string')
    except ET.ParseError:
        return (None, 'Invalid xml string')
    encrypt_str = encrypt_node.text
    to_username = to_username_node.text
    signature = sha1_encode(token, timestamp, nonce, encrypt_str)
    if signature <> msg_signature:
        return (None, 'Validation failed')
    encode_aes_key = base64.b64decode(aes_key + '=')
    if len(encode_aes_key) <> 32:
        return (None, 'Invalid EncodingAESKey string')
    cryptor = AES.new(encode_aes_key, AES.MODE_CBC, encode_aes_key[:16])
    plain_text = cryptor.decrypt(base64.b64decode(encrypt_str))
    pad = ord(plain_text[-1])
    content = plain_text[16: -pad]
    xml_len = socket.ntohl(struct.unpack('I', content[:4])[0])
    xml_content = content[4: xml_len + 4]
    incoming_appid = content[xml_len + 4:]
    if incoming_appid <> appid:
        return (None, 'Invalid APPID')
    return (xml_content, None)

def create_menu(menu_json, appid, appsecret):
    """ Configure WeChat Media Platform menu
    """
    access_token, err = fetch_access_token(appid, appsecret)
    if err is not None:
        return err
    json_context = json.dumps(menu_json, ensure_ascii=False).encode('utf-8')
    request_url = wechat_menu_create_url % access_token
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    try:
        resp = requests.post(request_url, data=json_context, headers=headers)
    except requests.RequestException:
        return 'Failed to connect to WeChat server'
    try:
        request_json = resp.json()
    except ValueError:
        return 'Unable to parse the response data from WeChat server'
    errcode = request_json.get('errcode', None)
    if errcode is not None and errcode <> 0:
        errmsg = request_json.get('errmsg', 'Unknown Error')
        return errmsg
    return None


complex_msg_template = """<xml>
    <ToUserName><![CDATA[@@TO_USERNAME]]></ToUserName>
    <FromUserName><![CDATA[@@FROM_USERNAME]]></FromUserName>
    <CreateTime>@@CREATE_TIME</CreateTime>
    <MsgType><![CDATA[news]]></MsgType>
    <ArticleCount>@@ARTICLE_COUNT</ArticleCount>
    <Articles>
        @@ARTICLES
    </Articles>
</xml>"""

article_template = """<item>
    <Title><![CDATA[@@TITLE]]></Title>
    <Description><![CDATA[@@DESCRIPTION]]></Description>
    <PicUrl><![CDATA[@@PICURL]]></PicUrl>
    <Url><![CDATA[@@URL]]></Url>
</item>"""

class Article(object):
    def __init__(self, title, desc, image, url):
        self.title = title
        self.desc = desc
        self.image = image
        self.url = url

def create_complex_msg(openid, wechat_id, articles):
    """ Create WeChat complex message
    Article:

    title: String
    desc: String
    image: String(Url)
    url: String
    """
    if articles is None or len(articles) == 0:
        return None
    xml = complex_msg_template.replace('@@TO_USERNAME', openid)
    xml = xml.replace('@@FROM_USERNAME', wechat_id)
    now = int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())
    xml = xml.replace('@@CREATE_TIME', str(now))
    xml = xml.replace('@@ARTICLE_COUNT', str(len(articles)))
    items = []
    for article in articles:
        item_xml = article_template.replace('@@TITLE', article.title)
        item_xml = item_xml.replace('@@DESCRIPTION', article.desc)
        item_xml = item_xml.replace('@@PICURL', article.image)
        item_xml = item_xml.replace('@@URL', article.url)
        items.append(item_xml)
    return xml.replace('@@ARTICLES', ''.join(items))


text_msg_template = """<xml>
    <ToUserName><![CDATA[@@TO_USERNAME]]></ToUserName>
    <FromUserName><![CDATA[@@FROM_USERNAME]]></FromUserName>
    <CreateTime>@@CREATE_TIME</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[@@CONTENT]]></Content>
</xml>"""

def create_text_msg(openid, wechat_id, content):
    """ Create WeChat text message
    """
    if content is None:
        return None
    xml = text_msg_template.replace('@@TO_USERNAME', openid)
    xml = xml.replace('@@FROM_USERNAME', wechat_id)
    now = int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())
    xml = xml.replace('@@CREATE_TIME', str(now))
    xml = xml.replace('@@CONTENT', content)
    return xml

def nonceStr():
    return str(uuid.uuid1()).replace('-', '')

def generateSHA1Sign(d):
    """ Generate sha1 signature
    """
    l = d.items()
    l = filter(lambda t: t[1] is not None and len(t[1].strip()) > 0, l)
    l = map(lambda t: '%s=%s' % t, l)
    l = sorted(l)
    stringSignTemp = reduce(lambda _1, _2: '%s&%s' % (_1, _2), l)
    stringSignTemp = stringSignTemp.encode('utf8')
    sha1Sign = hashlib.sha1(stringSignTemp).hexdigest()
    return sha1Sign

def fetchJsApiTicket(appid, appsecret):
    (access_token, err) = fetch_access_token(appid, appsecret)
    if err is not None:
        return render_bad_request_response(303, err)
    try:
        request_url = wechat_fetch_jsapi_ticket_url % access_token
        resp = requests.get(request_url)
    except requests.RequestException:
        return ((None, None), 'Failed to connect to WeChat server')
    try:
        request_json = resp.json()
    except ValueError:
        return ((None, None), 'Unable to parse the response data from WeChat server')
    errcode = request_json.get('errcode', None)
    if errcode is None or errcode <> 0:
        errmsg = request_json.get('errmsg', None)
        return ((None, None), errmsg)
    ticket = request_json.get('ticket', None)
    expires_in = request_json.get('expires_in', None)
    if ticket is None or expires_in is None:
        return ((None, None), 'Unknown Error')
    return ticket

def createWXConfig(url, jsApiList, appid, appsecret):
    index = url.find('#')
    if index <> -1:
        url = url[:index + 1]
    NonceStr = nonceStr()
    jsapi_ticket = fetchJsApiTicket(appid, appsecret)
    timestamp = str(int(time.mktime(datetime.datetime.now().timetuple())))
    d = {
        'noncestr': NonceStr,
        'jsapi_ticket': jsapi_ticket,
        'timestamp': timestamp,
        'url': url
    }
    signature = generateSHA1Sign(d)
    dd = {
        'debug': False,
        'appId': appid,
        'timestamp': timestamp,
        'nonceStr': NonceStr,
        'signature': signature,
        'jsApiList': jsApiList
    }
    return dd