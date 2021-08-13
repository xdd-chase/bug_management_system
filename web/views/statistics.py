import collections

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from web import models


def statistics(request, project_id):
    """统计页面"""
    return render(request, 'web/statistics.html')


def priority_statistics(request, project_id):
    """按照优先级显示饼图"""
    # 找到所有问题，根据优先级分组，每个优先级统计出问题数量
    start = request.GET.get('start')
    end = request.GET.get('end')
    # 1构造字典

    data_dict = collections.OrderedDict()
    for key, text in models.Issues.priority_choices:
        data_dict[key] = {'name': text, 'y': 0}
    # 2去数据库中拿到所有问题的分组得到的数量,
    result = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start,
                                          create_datetime__lt=end).values('priority').annotate(ct=Count('id'))
    # 3把数据分组得到的数量更新到data_dict中
    print(result)
    for item in result:
        data_dict[item['priority']]['y'] = item['ct']
    return JsonResponse({'status': True, 'data': list(data_dict.values())})


def project_user_statistics(request, project_id):
    """项目成员每个人分配的任务数量"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    # 构造字典,以参与者id为key,
    # {
    #     '1': {
    #         'name': '参与者name',
    #         'status': {
    #             1: 0,
    #             2: 0,
    #             3: 0,
    #             4: 0,
    #             5: 0,
    #             6: 0,
    #             7: 0,
    #         }
    #     },
    #     '2': {
    #         'name': '参与者name',
    #         'status': {
    #             1: 0,
    #             2: 0,
    #             3: 0,
    #             4: 0,
    #             5: 0,
    #             6: 0,
    #             7: 0,
    #         }
    #     }
    # }
    # 定义一个有序字典
    all_user_dict = collections.OrderedDict()
    all_user_dict[request.bug_mgt.project.creator.id] = {
        'name': request.bug_mgt.project.creator.username,
        'status': {item[0]: 0 for item in models.Issues.status_choices}
    }
    all_user_dict[None] = {
        'name': '未指派',
        'status': {item[0]: 0 for item in models.Issues.status_choices}
    }
    # 1找出当前项目的所有参与者，添加到字典中
    user_list = models.ProjectUser.objects.filter(project_id=project_id)
    for item in user_list:
        all_user_dict[item.user_id] = {
            'name': item.user.username,
            'status': {item[0]: 0 for item in models.Issues.status_choices}
        }
    # 2找到所有相关的问题
    issues_list = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start,
                                               create_datetime__lt=end)
    for item in issues_list:
        if not item.assign:
            all_user_dict[None]['status'][item.status] += 1
        else:
            all_user_dict[item.assign_id]['status'][item.status] += 1
    # 3获取所有成员
    categories = [data['name'] for data in all_user_dict.values()]
    # 4构造字典
    """
    data_result_dict = {
        1:{'name': 新建, 'data':[2,3,4]}
        2:{'name': 处理中, 'data':[2,3,4]}
        3:{'name': 已解决, 'data':[2,3,4]}
        4:{'name': 已忽略, 'data':[2,3,4]}
        5:{'name': 已反馈, 'data':[2,3,4]}
        6:{'name': 已关闭, 'data':[2,3,4]}
        7:{'name': 重新打开, 'data':[2,3,4]}
    }
    """
    data_result_dict = collections.OrderedDict()
    for item in models.Issues.status_choices:
        data_result_dict[item[0]] = {'name': item[1], 'data': []}

    for key, text in models.Issues.status_choices:
        # key=1,text=新建
        for row in all_user_dict.values():
            count = row['status'][key]
            data_result_dict[key]['data'].append(count)

    # 返回的数据格式：
    """
    context = {
        'status': True,
        'data': {
            'categories': ['张三', '李四', '王二'],
            'series': [
                {
                    'name': '新建中',
                    'data': [1, 3, 3]
                }, {
                    'name': '处理中',
                    'data': [1, 3, 3]
                }, {
                    'name': '已解决',
                    'data': [1, 3, 3]
                },
            ]
        }
    }
    """
    context = {
        'status': True,
        'data': {
            'categories': categories,
            'series': list(data_result_dict.values())
        }
    }
    print(context)
    return JsonResponse(context)
