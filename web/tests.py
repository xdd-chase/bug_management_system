from django.test import TestCase

# Create your tests here.

# !/usr/bin/env python
# coding=utf-8
import datetime
import os

from sts.sts import Sts

if __name__ == '__main__':
    for item in range(30):
        today = (datetime.datetime.now() + datetime.timedelta(days=-item)).date()
        yesterday = (datetime.datetime.now() + datetime.timedelta(days=-(item + 1))).date()
        print(today)
        print(yesterday)
