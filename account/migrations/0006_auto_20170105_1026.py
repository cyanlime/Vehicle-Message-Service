# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-05 02:26
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_auto_20170104_1546'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wechat',
            name='head_portrait',
        ),
        migrations.RemoveField(
            model_name='wechat',
            name='name',
        ),
        migrations.AddField(
            model_name='wechat',
            name='info',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='wechat',
            name='syntime',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 8, 0)),
        ),
    ]
