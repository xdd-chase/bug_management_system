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
        self.project = None


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

    def process_view(self, request, view, args, keargs):
        # 中间件，此处要解决的问题是当进入每个项目查看详细时，判定如果点击了某个项目，则进入此项目的详细内容（概览，问题，文件，wiki等）
        # 此时我们通过路由可知，当匹配到/manage/时，则是进入了项目详细页面
        # 另外，之所以放在process_view而不是放在process_request中是因为只有通过process_request这个中间件后才进入路由进行匹配
        # 所以要想拿到/manage/，只能在路由匹配完后才能拿到，即放在process_view方法中判断
        if not request.path_info.startswith('/manage/'):
            return
        # 如果匹配了/manage/，进行下一步，根据后面-匹配的ID进入确定的项目，此时还要防止用户直接在网址栏中直接写id（如9999，此ID数据库不存在）
        # 此时我们在查询数据库时加上creator参数或uer参数
        project_id = keargs.get('project_id')
        # 是否是我创建的
        project_object = models.Project.objects.filter(creator=request.bug_mgt.user, id=project_id).first()
        if project_object:
            # 是我创建的话，则让他通过
            request.bug_mgt.project = project_object
            return
        # 是否是我参与的项目
        project_uer_object = models.ProjectUser.objects.filter(user=request.bug_mgt.user, project_id=project_id).first()
        if project_uer_object:
            # 是我参与的话，则让他通过
            request.bug_mgt.project = project_uer_object.project
            return
        # 否则不让他通过，重定向到/project_list/
        return redirect('project_list')
