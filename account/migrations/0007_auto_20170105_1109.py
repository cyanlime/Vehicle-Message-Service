# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-05 03:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_auto_20170105_1026'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wechat',
            name='bind',
            field=models.BooleanField(default=False),
        ),
    ]
