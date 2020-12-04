import datetime

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from web import models


class BgtMgt:
    """
    封装一下登录进来的用户信息和价格策略，方便后面取这两个值使用
    """
    def __init__(self):
        self.user = None
        self.price_policy = None


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """如果用户以登录，则request中赋值"""
        request.bug_mgt = BgtMgt()
        user_id = request.session.get('user_id', 0)
        user_object = models.UserInfo.objects.filter(id=user_id).first()
        request.bug_mgt.user = user_object

        # 白名单，没有登录都可以访问的url
        """
        1. 获取当前用户访问的url
        2. 检查url是否在白名单中，如果在则继续访问，否则要进行判断是否登录
        """
        if request.path_info in settings.WHITE_REGEX_URL_LIST:
            return
        if not request.bug_mgt.user:
            return redirect('login')
        # 登录成功后，访问后台管理时，获取当前用户拥有的额度
        # 方式一：免费额度在交易记录中存储
        # 获取当前用户ID值最大的那条记录（在这里需要判断用户使用权限是否过期）
        _object = models.Transaction.objects.filter(user=user_object, status=2).order_by('-id').first()
        current_time = datetime.datetime.now()
        # 判断是否过期,对于免费版的end_datetime为0，所以要多判断一个条件
        if _object.end_datetime and _object.end_datetime < current_time:
            # 判断成立则为过期，此时需要切换成免费版给用户用
            _object = models.Transaction.objects.filter(user=user_object, status=2).order_by('id').first()
        request.bug_mgt.price_policy = _object.price_policy
