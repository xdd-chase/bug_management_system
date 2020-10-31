from django.core.validators import RegexValidator
from django.shortcuts import render, HttpResponse
from django_redis import get_redis_connection

from utils.tencent.sms import send_sms_single
from django.conf import settings
import random


def send_sms(request):
    """
    发送短信
    ?tpl=login -> 758917
    ?tpl=register -> 758918
    :param request:
    :return:
    """
    tpl = request.GET.get('tpl')
    template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
    if not template_id:
        return HttpResponse("模板不存在")
    code = random.randrange(1000, 9999)
    res = send_sms_single('15734068323', template_id, [code, ])
    if res['result'] == 0:
        return HttpResponse('成功')
    else:
        return HttpResponse(res['errmsg'])


from django import forms
from mgt import models


class RegisterModelForm(forms.ModelForm):
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator("1[345678]\d{9}",
                                                                           message='请输入正确格式的手机号码！')])
    password = forms.CharField(label='密码', widget=forms.PasswordInput())
    confirm_password = forms.CharField(label='重复密码', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    code = forms.CharField(label='验证码')

    class Meta:
        model = models.UserInfo
        # 设置参数为__all__时，则modelform显示的顺序为显示model里面的userinfo顺序，再是重写过的字段的顺序
        # fields = "__all__"
        # 当需要指定顺序时，则需自定义参数
        fields = ['username', 'email', 'password', 'confirm_password', 'mobile_phone', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():  # name代表当前字段的name，fields则代表每个字段后面的对象
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


def register(request):
    form = RegisterModelForm()
    return render(request, 'register.html', {'form': form})


def index(request):
    # 去连接池中获取一个连接
    conn = get_redis_connection("default")  # default为local_settings配置文件中的CACHES中的一个键default
    conn.set('nickname', "***", ex=10)
    value = conn.get('nickname')
    print(value)
    return HttpResponse("OK")
