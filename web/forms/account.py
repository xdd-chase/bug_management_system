import random
import re
from utils import encrypt
from utils.tencent.sms import send_sms_single
from django import forms
from django_redis import get_redis_connection
from django.conf import settings
from django.core.exceptions import ValidationError

from web import models
from django.core.validators import RegexValidator


class BootStrapForm(object):
    """BootStrap基类，给需要的字段添加class样式"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():  # name代表当前字段的name，fields则代表每个字段后面的对象
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


class RegisterModelForm(BootStrapForm, forms.ModelForm):
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

    def clean_username(self):
        username = self.cleaned_data['username']
        exists = models.UserInfo.objects.filter(username=username).exists()
        if exists:
            raise ValidationError('用户名已存在')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        exists = models.UserInfo.objects.filter(email=email).exists()
        if exists:
            raise ValidationError('邮箱已存在')
        return email

    def clean_password(self):
        # 密码长度限制
        password = self.cleaned_data['password']
        if len(password.strip()) < 6 or len(password.strip()) > 18:
            raise ValidationError('密码长度要在6~18位之间')
        # 加密，返回
        return encrypt.md5(password)

    def clean_confirm_password(self):
        try:
            print(self.cleaned_data)
            password = self.cleaned_data['password']
            confirm_password = encrypt.md5(self.cleaned_data['confirm_password'])
            if password != confirm_password:
                raise ValidationError('两次密码不一致')
        except KeyError as e:
            raise ValidationError('密码不符合要求')
        return encrypt.md5(confirm_password)

    def clean_mobile_phone(self):
        # 手机号也要校验，防止在发送验证码完成校验后，又误操作了删除或改动了手机号出现问题
        mobile_phone = self.cleaned_data['mobile_phone']
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if exists:
            raise ValidationError('手机号已注册')
        ret = re.match(r"^1[35678]\d{9}$", mobile_phone)
        if not ret:
            raise ValidationError('手机号格式不正确')
        return mobile_phone

    def clean_code(self):
        code = self.cleaned_data['code']
        mobile_phone = self.cleaned_data.get('mobile_phone')
        if not mobile_phone:
            return code
        #  连接Redis
        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)
        if not redis_code:
            raise ValidationError('验证码失效或未发送，请重新发送')
        #  验证码匹配成功后，由于在Redis中存入的是byte类型，则要解码
        redis_str_code = redis_code.decode('utf-8')
        if code.strip() != redis_str_code:
            raise ValidationError('验证码错误，请重新输入')
        return code


class SendSmsForm(forms.Form):
    mobile_phone = forms.CharField(label='手机号')

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_mobile_phone(self):
        """手机号校验的钩子"""
        mobile_phone = self.cleaned_data['mobile_phone']
        print(">>",mobile_phone)
        # 判断短信模板是否有问题
        tpl = self.request.GET.get('tpl')
        template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
        if not template_id:
            raise ValidationError('短信模板错误')
        # 手机号格式校验
        ret = re.match(r"^1[35678]\d{9}$", mobile_phone)
        if not ret:
            raise ValidationError('手机号格式不正确')
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if tpl == 'login':
            # 若tpl == 'login'则为短信验证登录
            if not exists:
                raise ValidationError('手机号不存在，请注册')
        else:
            # 当tpl==register,校验数据库中是否存在此电话号码
            if exists:
                raise ValidationError('手机号已存在')
        code = random.randrange(1000, 9999)
        # 发送短信
        sms = send_sms_single(mobile_phone, template_id, [code, ])
        if sms['result'] != 0:
            raise ValidationError("短信发送失败，{}".format(sms['errmsg']))
        # 验证码写入redis（Django Redis）
        conn = get_redis_connection()
        conn.set(mobile_phone, code, ex=60)
        return mobile_phone


class LoginSmsForm(BootStrapForm, forms.Form):
    mobile_phone = forms.CharField(
        label='手机号',
        validators=[RegexValidator(r"^1[35678]\d{9}$", message='请输入正确格式的手机号码！')])
    code = forms.CharField(label='验证码')

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        # 直接获取手机用户，若存在直接返回一个用户对象，而不用再次去查询数据库获取用户
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if not exists:
            raise ValidationError('手机号不存在')
        return mobile_phone

    def clean_code(self):
        code = self.cleaned_data['code']
        mobile_phone = self.cleaned_data.get('mobile_phone')
        # 手机号不存在，则无需再校验验证码
        if not mobile_phone:
            return code
        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)
        if not redis_code:
            raise ValidationError('验证码失效或未发送，请重新发送')
        #  验证码匹配成功后，由于在Redis中存入的是byte类型，则要解码
        redis_str_code = redis_code.decode('utf-8')
        if code.strip() != redis_str_code:
            raise ValidationError('验证码错误，请重新输入')
        return code


class LoginForm(BootStrapForm, forms.Form):
    username = forms.CharField(label='手机号或邮箱')
    password = forms.CharField(label='密码', widget=forms.PasswordInput())
    code = forms.CharField(label='图片验证码')

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_password(self):
        password = self.cleaned_data['password']
        # 加密，返回
        return encrypt.md5(password)

    def clean_code(self):
        code = self.cleaned_data['code']
        session_code = self.request.session.get('image_code')
        if not session_code:
            raise ValidationError('验证码已过期，请重新输入')
        if code.strip().upper() != session_code.upper():
            raise ValidationError('验证码输入错误')
        return code
