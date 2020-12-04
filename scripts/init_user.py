import base
from web import models

models.UserInfo.objects.create(username='aa', email='ss@123.com', mobile_phone='13244444444', password='123456')
