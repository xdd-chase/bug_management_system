from django import template
from web import models
from django.urls import reverse

register = template.Library()


@register.inclusion_tag('inclusion/all_project_list.html')
def all_project_list(request):
    # 获取我创建的项目
    my_project_list = models.Project.objects.filter(creator=request.bug_mgt.user)
    # 获取我参与的项目
    join_project_list = models.ProjectUser.objects.filter(user=request.bug_mgt.user)
    return {'my': my_project_list, 'join': join_project_list, 'request': request}


@register.inclusion_tag('inclusion/manage_menu_list.html')
def manage_menu_list(request):
    data_list = [
        {'title': '概述', 'url': reverse('dashboard', kwargs={'project_id': request.bug_mgt.project.id})},
        {'title': '问题', 'url': reverse('issues', kwargs={'project_id': request.bug_mgt.project.id})},
        {'title': '统计', 'url': reverse('statistics', kwargs={'project_id': request.bug_mgt.project.id})},
        {'title': 'Wiki', 'url': reverse('wiki', kwargs={'project_id': request.bug_mgt.project.id})},
        {'title': '文件', 'url': reverse('file', kwargs={'project_id': request.bug_mgt.project.id})},
        {'title': '配置', 'url': reverse('setting', kwargs={'project_id': request.bug_mgt.project.id})}
    ]
    for item in data_list:
        # 当前用户访问的url：request.path_info /manage/4/issues/xxx/add
        if request.path_info.startswith(item['url']):
            item['class'] = 'active'
    return {'data_list': data_list}
