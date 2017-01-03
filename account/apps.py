from __future__ import unicode_literals

import os, sys, json, codecs
from django.apps import AppConfig
from . import settings
import wechat

class RegMenuError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return repr('Failed to create menu, internal error: %s' % self.errmsg)

class AccountConfig(AppConfig):
    name = 'account'

    def load_menu_json(self):
        dirname = os.path.split(os.path.realpath(__file__))[0]
        filename = os.path.join(dirname, 'menu.json')
        try:
            with codecs.open(filename, 'r', 'utf-8') as f:
                json_str = f.read()
                json_str = json_str.replace(u'@@HOSTNAME', settings.HOSTNAME)
            return (json_str, None)
        except IOError, e:
            return (None, e)

    def reg_menu(self):
        (menu_json_str, err) = self.load_menu_json()
        if err is not None:
            raise RegMenuError(err)
        try:
            menu_json = json.loads(menu_json_str)
        except TypeError:
            raise RegMenuError('Unable to parse the json string')
        err = wechat.create_menu(menu_json, settings.APP_ID, settings.APP_SECRET)
        if err is not None:
            raise RegMenuError(err)

    def ready(self):
        # Refer https://docs.djangoproject.com/en/dev/ref/applications/#django.apps.AppConfig.ready
        cmd = sys.argv[1]
        if cmd == 'runserver':
            self.reg_menu()