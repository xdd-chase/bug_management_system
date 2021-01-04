from django import template
from web import models

register = template.Library()


@register.inclusion_tag('inclusion/all_project_list.html')
def all_project_list(request):
    # 获取我创建的项目
    my_project_list = models.Project.objects.filter(creator=request.bug_mgt.user)
    # 获取我参与的项目
    join_project_list = models.ProjectUser.objects.filter(user=request.bug_mgt.user)
    return {'my': my_project_list, 'join': join_project_list}
