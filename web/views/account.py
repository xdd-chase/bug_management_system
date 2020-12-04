"""
有关账户功能的视图: 登录，注册，验证，注销等
"""
import datetime
import uuid

from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Q
from web.forms.account import RegisterModelForm, SendSmsForm, LoginSmsForm, LoginForm
from web import models


def register(request):
    """注册"""
    if request.method == 'GET':
        print(123)
        form = RegisterModelForm()
        return render(request, 'web/register.html', {'form': form})
    if request.method == 'POST':
        # 实例化modelform表单，对每个注册字段进行校验
        form = RegisterModelForm(data=request.POST)
        if form.is_valid():
            # 验证通过，写入数据库,通过form.save()，将model模型中定义的字段写入数据库，modelform中其他的字段丢弃，如code等
            # 密码必须是加密的
            instance = form.save()
            price_policy_obj = models.PricePolicy.objects.filter(category=1,title='个人免费版').first()
            # 创建一条交易记录
            models.Transaction.objects.create(
                status=2,
                order=str(uuid.uuid4()),
                user=instance,
                price_policy=price_policy_obj,
                count=0,
                price=0,
                start_datetime=datetime.datetime.now()
            )
            return JsonResponse({'status': True, 'data': '/login/'})
        else:
            return JsonResponse({'status': False, 'error': form.errors})


def send_sms(request):
    """发送短信"""
    form = SendSmsForm(request, data=request.GET)
    if form.is_valid():
        return JsonResponse({'status': True})
    # form.errors方法则是返回form中所有的异常结果
    return JsonResponse({'status': False, 'error': form.errors})


def login_sms(request):
    """短信登录"""
    if request.method == 'GET':
        form = LoginSmsForm()
        return render(request, 'web/login_sms.html', {'form': form})
    form = LoginSmsForm(request.POST)
    if form.is_valid():
        # 登录成功
        mobile_phone = form.cleaned_data['mobile_phone']
        # 把用户名写入到session中
        user_object = models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()
        request.session['user_id'] = user_object.id
        request.session.set_expiry(60 * 60 * 24 * 14)
        return JsonResponse({"status": True, "data": "/index/"})
    return JsonResponse({"status": False, "error": form.errors})


def login(request):
    """用户名密码登录"""
    if request.method == 'GET':
        form = LoginForm(request)
        return render(request, 'web/login.html', {'form': form})
    form = LoginForm(request, data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        # user_object = models.UserInfo.objects.filter(username=username, password=password).first()
        user_object = models.UserInfo.objects.filter(Q(email=username) | Q(mobile_phone=username)).filter(
            password=password).first()
        if user_object:
            # 用户名密码正确，登录成功
            request.session['user_id'] = user_object.id
            # 设置过期时间
            request.session.set_expiry(60 * 60 * 24 * 14)
            return redirect('index')
        form.add_error('username', '用户名或密码错误')
    return render(request, 'web/login.html', {'form': form})


def logout(request):
    request.session.flush()
    return redirect('index')


def image_code(request):
    """生成验证码"""
    from utils.img_code import check_code
    from io import BytesIO
    image_object, code = check_code()
    # 将验证码写入到session中，并设置过期时间为60秒，默认过期时间为两星期
    request.session['image_code'] = code
    request.session.set_expiry(60)
    stream = BytesIO()
    image_object.save(stream, 'png')
    return HttpResponse(stream.getvalue())
