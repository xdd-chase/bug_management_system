from django.shortcuts import render, HttpResponse
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

