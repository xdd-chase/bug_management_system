"""
有关后台管理中的项目查看，新建等功能
"""
from django.shortcuts import render


def project_list(request):
    """项目列表"""
    print(request.bug_mgt.user)
    print(request.bug_mgt.price_policy)
    return render(request, 'web/project_list.html')
