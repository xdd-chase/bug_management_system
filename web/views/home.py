import datetime
import json

from django.shortcuts import render, redirect, HttpResponse
from django_redis import get_redis_connection
from django.conf import settings
from utils.encrypt import uid
from web import models
from utils.alipay import AliPay


def index(request):
    return render(request, 'web/index.html')


def prices(request):
    policy_list = models.PricePolicy.objects.filter(category=2)
    return render(request, 'web/prices.html', {'policy_list': policy_list})


def payment(request, policy_id):
    """
    支付页面
    """
    # 验证价格策略套餐是否存在
    policy_object = models.PricePolicy.objects.filter(id=policy_id, category=2).first()
    if not policy_object:
        return redirect('prices')
    # 验证要购买的数量
    number = request.GET.get('number', '')
    if not number or not number.isdecimal():
        return redirect('prices')
    number = int(number)
    if number < 1:
        return redirect('prices')
    # 计算原价
    origin_price = number * policy_object.price
    # 之前购买的套餐
    balance = 0
    _object = None
    if request.bug_mgt.price_policy.category == 2:
        # 找到之前的订单，如果有，则查出最新的订单，拿到开始时间和结束时间，再根据当前时间计算出剩余时间，进行抵扣
        _object = models.Transaction.objects.filter(user=request.bug_mgt.user, status=2).order_by('-id').first()
        total_time = _object.end_datetime - _object.start_datetime
        balance_time = _object.end_datetime - datetime.datetime.now()
        if total_time.days == balance_time.days:
            # 若用户购买了套餐，立刻再次购买，则抵扣天数减1
            balance = _object.price / total_time.days * (balance_time.days - 1)
        else:
            balance = _object.price / total_time.days * balance_time.days
    if balance >= origin_price:
        return redirect('prices')
    context = {
        'policy_id': policy_object.id,
        'number': number,  # 购买数量
        'origin_price': origin_price,  # 原价
        'balance': round(balance, 2),  # 折扣,保留两位小数
        'total_price': origin_price - round(balance, 2)  # 支付价格
    }
    conn = get_redis_connection()
    key = 'payment_{}'.format(request.bug_mgt.user.mobile_phone)
    conn.set(key, json.dumps(context), ex=30 * 60)  # redis缓存，30分钟失效
    context['policy_object'] = policy_object
    context['transaction'] = _object
    return render(request, 'web/payment.html', context)


'''
def pay(request):
    """支付，生成订单"""
    # 通过redis取出购买的套餐数据，进行判断
    conn = get_redis_connection()
    key = 'payment_{}'.format(request.bug_mgt.user.mobile_phone)
    context_string = conn.get(key)
    if not context_string:
        return redirect('prices')
    context = json.loads(context_string.decode('utf-8'))
    # 数据库中生成交易记录（未支付），支付成功之后将订单状态更新为已支付，开始时间和结束时间更新
    order_id = uid(request.bug_mgt.user.mobile_phone)
    total_price = context['total_price']
    models.Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.bug_mgt.user,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=total_price
    )
    # 跳到支付页面去支付
    # -生成支付链接，跳转到这个链接
    # 网关由地址+参数组成
    # 网关地址： https://openapi.alipaydev.com/gateway.do
    """
    'return_url': "http://127.0.0.1:8001/prices/pay/notify/",
        'notify_url': "http://127.0.0.1:8001/prices/pay/notify/",
    params = {
        app_id: "2021000117694725",
        method: "alipay.trade.page.pay",
        format: "JSON",
        charset: "utf-8",
        sign_type："RSA2",
        sign: "签名",
        timestamp: "",
        version: "1.0",
        'return_url': "支付成功后发送get请求，跳转到那个页面",
        'notify_url': "支付成功后同时发送一个post请求，更新订单",
        biz_content: {
            out_trade_no: "订单编号",
            scene: "bar_code",
            auth_code: "支付授权码",
            product_code: "FACE_TO_FACE_PAYMENT",
            subject: "订单标题",
            total_amount: "12.2"
        }
    }
    """
    """
    生成签名：
    1.将参数中的空，文件，字节，sign 剔除， params.pop(sign)
    2.排序，对参数中的所有的key，从大到小排序，sort（params）
        并按照第一个字符ASCII码升序排序，相同字母依次按照后面的字母排序
    3.将排序后的参数与其对应值，组合成"参数=参数值"的格式，将这些参数用&连接起来，此字符串则为待签名字符串
        "app_id=2021000117694725&method=alipay.trade.pay"
        注意：有字典要转换为字符串；字符串中间不能有空格，使用json.dumps(info,separators=(",",":"))方法将逗号和冒号后面的空格去掉
    4.使用各自语言对应的 SHA256WithRSA(对应sign_type为RSA2)签名函数利用商户私钥对待签名字符串进行签名，并进行 Base64 编码。
        result = 使用SHA256WithRSA签名函数利用商户私钥对待签名字符串进行签名
        签名 = result进行 Base64 编码
    再把签名加入到params字典中，params[sign] = 签名
    注意：Base64编码之后，  内部不能有换行字符，签名.replace("\n", "")
    5.再将所有的参数拼接起来
        注意：在拼接url时，不能出现；，（）等字符，需要提前转义,导入一下模块解决
        from urllib.parse import quote_plus
    
    """
    params = {
        'app_id': "2021000117694725",
        'method': "alipay.trade.page.pay",
        'format': "JSON",
        'charset': "utf-8",
        'sign_type': "RSA2",
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'version': "1.0",
        'biz_content': json.dumps({
            'out_trade_no': order_id,
            'product_code': "FACE_TO_FACE_PAYMENT",
            'total_amount': 1.11,
            'subject': "SSVIP"
        }, separators=(',', ':'))
    }
    # 待签名字符串
    unsigned_str = "&".join(["{0}={1}".format(k, params[k]) for k in sorted(params)])
    # SHA256WithRSA签名
    from Crypto.PublicKey import RSA
    from base64 import decodebytes, encodebytes
    from Crypto.Signature import PKCS1_v1_5  # 用于签名/验签
    from Crypto.Hash import SHA256
    # SHA256WithRSA + 应用私钥 对待签名字符串签名
    private_key = RSA.importKey(open('files/应用私钥_RSA2_PKCS1.txt').read())
    signer = PKCS1_v1_5.new(private_key)
    signature = signer.sign(SHA256.new(unsigned_str.encode('utf-8')))
    # 对签名进行base64编码，再转化为字符串
    sign_str = encodebytes(signature).decode('utf-8').replace('\n', '')
    # 把生成的签名赋值给sign，拼接到参数中
    from urllib.parse import quote_plus
    result = "&".join(["{0}={1}".format(k, quote_plus(params[k])) for k in sorted(params)])
    result = result + "&sign=" + quote_plus(sign_str)
    gateway = "https://openapi.alipaydev.com/gateway.do"
    pay_url = "{0}?{1}".format(gateway, result)
    return redirect(pay_url)
'''


def pay(request):
    """支付，生成订单"""
    # 通过redis取出购买的套餐数据，进行判断
    conn = get_redis_connection()
    key = 'payment_{}'.format(request.bug_mgt.user.mobile_phone)
    context_string = conn.get(key)
    if not context_string:
        return redirect('prices')
    context = json.loads(context_string.decode('utf-8'))
    # 数据库中生成交易记录（未支付），支付成功之后将订单状态更新为已支付，开始时间和结束时间更新
    order_id = uid(request.bug_mgt.user.mobile_phone)
    total_price = context['total_price']
    models.Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.bug_mgt.user,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=total_price
    )
    # 生成支付链接
    ali_pay = AliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=settings.ALIPAY_NOTIFY_URL,
        return_url=settings.ALIPAY_RETURN_URL,
        app_private_key_path=settings.ALIPAY_PRIVATE_KEY_PATH,
        alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH
    )
    query_params = ali_pay.direct_pay(
        subject="系统会员",
        out_trade_no=order_id,
        total_amount=total_price
    )
    pay_url = "{0}?{1}".format(settings.GATEWAY, query_params)
    return redirect(pay_url)


def notify(request):
    """支付成功后跳转的url"""
    ali_pay = AliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=settings.ALIPAY_NOTIFY_URL,
        return_url=settings.ALIPAY_RETURN_URL,
        app_private_key_path=settings.ALIPAY_PRIVATE_KEY_PATH,
        alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH
    )
    # 在正式环境中，支付成功后，get请求只做跳转，不做订单更新，订单更新需要放在post请求中，在这里我们只测试，所以放在了get方法中
    # 当支付成功后，支付宝会将订单号返回，获取订单号，根据订单号做状态更新和返回值验证（是否是支付宝的返回值）
    # 此时会通过支付宝公钥对request请求中的值做检查，通过表示为支付宝发送过来的返回值
    if request.method == 'GET':
        params = request.GET.dict()
        sign = params.pop('sign', None)
        status = ali_pay.verify(params, sign)
        if status:
            out_trade_no = params['out_trade_no']
            _object = models.Transaction.objects.filter(order=out_trade_no).first()
            _object.status = 2
            _object.start_datetime = datetime.datetime.now()
            _object.end_datetime = datetime.datetime.now() + datetime.timedelta(days=365 * _object.count)
            _object.save()
            return HttpResponse('支付完成')
        return HttpResponse('支付失败')
    else:
        from urllib.parse import parse_qs
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)
        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]
        sign = post_dict.pop('sign', None)
        status = ali_pay.verify(post_dict, sign)
        if status:
            out_trade_no = post_dict['out_trade_no']
            _object = models.Transaction.objects.filter(order=out_trade_no).first()
            _object.status = 2
            _object.start_datetime = datetime.datetime.now()
            _object.end_datetime = datetime.datetime.now() + datetime.timedelta(days=365 * _object.count)
            _object.save()
            return HttpResponse('success')

    return HttpResponse("error")
