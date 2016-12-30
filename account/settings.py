""" Account Settings
"""

import os, datetime
from django.conf import settings as django_settings

JWT_EXPIRATION_DELTA = \
    getattr(django_settings, 'JWT_EXPIRATION_DELTA', datetime.timedelta(days=365))

APP_ID = os.getenv('VMS_APP_ID')
APP_SECRET = os.getenv('VMS_APP_SECRET')

WECHAT_TOKEN = os.getenv('VMS_WECHAT_TOKEN')