import collections

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
import datetime
import time
from web import models


def dashboard(request, project_id):
    """概览"""

    # 问题数据处理
    status_dict = {}
    for key, text in models.Issues.status_choices:
        status_dict[key] = {'text': text, 'count': 0}
    # 将查询到的数据根据status分组，再计算每组的数量赋值给ct
    issue_data = models.Issues.objects.filter(project_id=project_id).values('status').annotate(ct=Count('id'))
    for item in issue_data:
        status_dict[item['status']]['count'] = item['ct']

    # 项目成员
    user_list = models.ProjectUser.objects.filter(project_id=project_id).values('user_id', 'user__username')

    # 最近的10个问题
    top_ten = models.Issues.objects.filter(project_id=project_id, assign__isnull=False).order_by('-id')[0:10]
    context = {
        'status_dict': status_dict,
        'user_list': user_list,
        'top_ten_object': top_ten
    }
    return render(request, 'web/dashboard.html', context)


def issues_chart(request, project_id):
    """在后端生成highcharts所需要的数据"""
    # 最近30天每天新建问题的数量
    # 去数据库查询出最近30天的所有数据(create_datetime__gte=today - datetime.timedelta(days=30))
    # 根据日期分组（分组用annotate（）方法）
    today = datetime.datetime.now().date()  # 获取当天的年月日
    date_dict = collections.OrderedDict()  # 生成一个有序字典
    for i in range(0, 30):
        date = today - datetime.timedelta(days=i)  # date 就代表从当天往前第i天的日期
        # 再将date转化为字符型，再格式化为时间戳
        date_dict[date.strftime("%Y-%m-%d")] = [time.mktime(date.timetuple()) * 1000, 0]
    # 经过for循环初始化后得到的date_dict的格式为：
    # {
    # "2021-1-1":[2034978239047, 0],
    # "2021-1-2":[2341412342134, 0],
    # "2021-1-3":[2135412352345, 0],
    # "2021-1-4":[2354134334524, 0],
    # }
    # 前端需要的格式为[
    # [2034978239047, 0],
    # [2034978239042, 0],
    # [2034978239044, 0],
    # [2034978239046, 0],
    # ]
    result = models.Issues.objects.filter(project_id=project_id,
                                          create_datetime__gte=today - datetime.timedelta(days=30)).extra(
        select={"ctime": "DATE_FORMAT(web_issues.create_datetime, '%%Y-%%m-%%d')"}).values('ctime').annotate(
        ct=Count('id'))
    # result为[{'ctime': '2021-07-06', 'ct': 1}]
    # 为满足前端格式则对result处理
    for item in result:
        date_dict[item['ctime']][1] = item['ct']

    return JsonResponse({"status": True, "data": list(date_dict.values())})
    pass
