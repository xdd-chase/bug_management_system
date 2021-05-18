"""
有关后台管理中的项目查看，新建等功能
"""
import time
from django.shortcuts import render, redirect
from web.forms.project import ProjectModelForm
from django.http import JsonResponse, HttpResponse
from web import models
from utils.tencent import cos


def project_list(request):
    """项目列表"""
    if request.method == "GET":
        # get请求查看项目列表
        """
        1.从数据库中获取两部分数据
          我创建的所有项目：已星标、未星标
          我参与的所有项目：已星标、未星标
        2.提取已星标
          列表 = 循环[我创建的所有项目] + [我参与的所有项目]
          把已星标的数据提取   
          得到三个列表：星标、创建、参与
        """
        project_dict = {'star': [], 'my': [], 'join': []}
        my_project_list = models.Project.objects.filter(creator=request.bug_mgt.user)
        for row in my_project_list:
            if row.star:
                project_dict['star'].append({'value': row, 'type': 'my'})
            else:
                project_dict['my'].append({'value': row, 'type': 'my'})
        join_project_list = models.ProjectUser.objects.filter(user=request.bug_mgt.user)
        for item in join_project_list:
            if item.star:
                project_dict['star'].append({'value': item.project, 'type': 'join'})
            else:
                project_dict['join'].append({'value': item.project, 'type': 'join'})
        form = ProjectModelForm(request)
        return render(request, 'web/project_list.html', {'form': form, 'project_dict': project_dict})
    form = ProjectModelForm(request, data=request.POST)
    if form.is_valid():  # 只有当表单验证的数据都合法（例如手机号码验证等），is_valid()才等于True
        name = form.cleaned_data['name']
        # 为项目创建桶
        bucket = "{}-{}-{}-1259386016".format(name, request.bug_mgt.user.mobile_phone, str(int(time.time())))
        region = 'ap-nanjing'
        cos.create_bucket(bucket=bucket, region=region)
        # 验证通过后，则需要向数据库写入数据，此时project表中所必须填入的字段有
        # 项目名，颜色，描述，（项目使用空间，星标，项目参与人数，创建时间这些都有默认值，不需要赋值），创建者
        form.instance.creator = request.bug_mgt.user
        form.instance.bucket = bucket
        form.instance.region = region
        # 保存项目后返回一个对象
        instance = form.save()
        # 项目初始化问题类型
        issues_type_list = []
        for item in models.IssuesType.PROJECT_INIT_LIST:
            issues_type_list.append(models.IssuesType(project=instance, title=item))
        models.IssuesType.objects.bulk_create(issues_type_list)
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def project_star(request, project_type, project_id):
    """星标项目"""
    if project_type == 'my':
        # 为防止用户在网址栏直接改project_id，所以要增加creator=request.bug_mgt.user限制条件
        models.Project.objects.filter(id=project_id, creator=request.bug_mgt.user).update(star=True)
        return redirect('project_list')
    if project_type == 'join':
        models.ProjectUser.objects.filter(id=project_id, creator=request.bug_mgt.user).update(star=True)
        return redirect('project_list')
    return HttpResponse('请求错误')


def project_unstar(request, project_type, project_id):
    """取消星标"""
    if project_type == 'my':
        # 为防止用户在网址栏直接改project_id，所以要增加creator=request.bug_mgt.user限制条件
        models.Project.objects.filter(id=project_id, creator=request.bug_mgt.user).update(star=False)
        return redirect('project_list')
    if project_type == 'join':
        models.ProjectUser.objects.filter(id=project_id, creator=request.bug_mgt.user).update(star=False)
        return redirect('project_list')
    return HttpResponse('请求错误')
