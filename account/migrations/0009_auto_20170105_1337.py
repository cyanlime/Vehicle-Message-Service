# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-05 13:37
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0008_auto_20170105_1330'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wechat',
            name='syntime',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 8, 0)),
        ),
    ]
