# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-03 10:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_article'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wechat',
            options={'verbose_name': 'WeChat'},
        ),
    ]
