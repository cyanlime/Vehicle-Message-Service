""" Account Settings
"""

import os, datetime
from django.conf import settings as django_settings

JWT_EXPIRATION_DELTA = \
    getattr(django_settings, 'JWT_EXPIRATION_DELTA', datetime.timedelta(days=365))

APP_ID = os.getenv('VMS_APP_ID')
APP_SECRET = os.getenv('VMS_APP_SECRET')

WECHAT_TOKEN = os.getenv('VMS_WECHAT_TOKEN')
ENCODING_AES_KEY = os.getenv('VMS_ENCODING_AES_KEY')

HOSTNAME = os.getenv('VMS_HOSTNAME')
HOSTNAME_WITH_SCHEMA = 'http://%s' % HOSTNAME