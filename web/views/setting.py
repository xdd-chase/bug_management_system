from django.shortcuts import render, redirect
from utils.tencent.cos import delete_bucket
from web import models


def setting(request, project_id):
    return render(request, 'web/setting.html')


def delete(request, project_id):
    """删除项目"""
    if request.method == 'GET':
        return render(request, 'web/setting_delete.html')
    project_name = request.POST.get('project_name')
    if not project_name or project_name != request.bug_mgt.project.name:
        return render(request, 'web/setting_delete.html', {'error': "项目名错误"})
    # 项目名写对了则从数据库中删除（只有创建者才能删除当前项目）
    if request.bug_mgt.user != request.bug_mgt.project.creator:
        return render(request, 'web/setting_delete.html', {'error': "只有项目创建者才能删除项目"})
    # 删除桶
    #   -删除桶中的所有文件（找到桶，再删除桶中所有的文件）
    #   -删除桶中的所有碎片，（当上传很大文件的过程中中断网页等操作，会产生文件碎片）
    # 删除项目
    delete_bucket(request.bug_mgt.project.bucket, request.bug_mgt.project.region)
    models.Project.objects.filter(id=request.bug_mgt.project.id).delete()

    return redirect("project_list")
