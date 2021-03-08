from django.shortcuts import render
from django.http import JsonResponse
from web import models
from web.forms.file import FileModelForm
from utils.tencent.cos import delete_file, delete_file_list, credential


def file(request, project_id):
    parent_object = None
    folder_id = request.GET.get('folder_id', "")
    if folder_id.isdecimal():
        # 拿到当前文件夹的id，判断数据库中是否存在，存在则将此文件夹作为父目录，当用户通过此文件夹点击进入时，则在下一步进行筛选出
        # 当前文件夹id下属的所有文件夹和文件
        parent_object = models.FileRepository.objects.filter(id=int(folder_id), file_type=2,
                                                             project=request.bug_mgt.project).first()

    if request.method == 'GET':
        # 用于存放导航栏中文件夹的层级目录，返回给前端展示出文件夹导航效果
        breadcrumb_list = []
        parent = parent_object
        if parent:
            # 把当前点击的文件夹赋值给parent，然后循环找出这个点击的文件夹的父级文件夹，一直找到根目录，再依次添加到列表中返回前台
            while parent:
                breadcrumb_list.insert(0, {'id': parent.id, 'name': parent.file_name})
                parent = parent.parent
        queryset = models.FileRepository.objects.filter(project=request.bug_mgt.project)
        # 展示当前目录下的文件和文件夹，若有父级文件夹，则将当前文件夹下的目录展现，若没有，则展示根目录下的文件和文件夹
        if parent_object:
            file_object_list = queryset.filter(parent=parent_object).order_by('-file_type')  # 以文件夹、文件的形式排列
        else:
            file_object_list = queryset.filter(parent_id__isnull=True).order_by('-file_type')
        form = FileModelForm(request, parent_object)
        context = {
            'form': form,
            'file_object_list': file_object_list,
            'breadcrumb_list': breadcrumb_list
        }
        return render(request, 'web/file.html', context)
    # post提交，用户新建文件夹
    # 由于是共用一个post提交,编辑和添加文件夹则需要做区分，通过前台是否传过来fid来判断是编辑还是添加，若fid存在,则为编辑
    fid = request.POST.get('fid', '')
    edit_object = None
    if fid.isdecimal():
        # 获取编辑文件夹对象
        edit_object = models.FileRepository.objects.filter(id=int(fid), file_type=2,
                                                           project=request.bug_mgt.project).first()
    if edit_object:
        # 如果存在，则为编辑文件夹，此时传入一个instance对象（已在数据库中获取到了），通过modelform做校验，通过后就save
        form = FileModelForm(request, parent_object, data=request.POST, instance=edit_object)
    else:
        # 不存在则为添加文件夹
        form = FileModelForm(request, parent_object, data=request.POST)
    if form.is_valid():
        form.instance.project = request.bug_mgt.project
        form.instance.file_type = 2
        form.instance.update_user = request.bug_mgt.user
        form.instance.parent = parent_object
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def file_delete(request, project_id):
    """删除文件"""
    fid = request.GET.get('fid')
    # 删除数据库中的文件和文件夹（内部已经包含级联删除）
    delete_object = models.FileRepository.objects.filter(id=fid, project=request.bug_mgt.project).first()
    if delete_object.file_type == 1:
        # 删除文件(数据库文件删除，cos文件删除，项目已使用空间回收)
        # 释放空间
        request.bug_mgt.project.used_space -= delete_object.size
        request.bug_mgt.project.save()
        # cos中删除文件
        delete_file(request.bug_mgt.project.bucket, request.bug_mgt.project.region, delete_object.key)
        # 在数据库中删除文件
        delete_object.delete()
        return JsonResponse({'status': True})
    else:
        # 删除文件夹(找到文件夹下所有文件->数据库文件删除，cos文件删除，项目已使用空间回收)
        # 设置总的释放空间的变量
        total_size = 0
        # 设置用于存放要删除的文件的唯一文件名
        key_list = []
        # 设置文件夹集合，用于存放要遍历的文件夹
        folder_list = [delete_object, ]
        for folder in folder_list:
            child_list = models.FileRepository.objects.filter(project=request.bug_mgt.project, parent=folder).order_by(
                '-file_type')
            for child in child_list:
                if child.file_type == 2:
                    folder_list.append(child)
                else:
                    # 否则的话就是文件，对文件大小汇总
                    total_size += child.size
                    # 删除文件
                    key_list.append({'Key': child.key})
        # cos中删除文件
        if key_list:
            delete_file_list(request.bug_mgt.project.bucket, request.bug_mgt.project.region, key_list)
        # 释放空间
        if total_size:
            request.bug_mgt.project.used_space -= total_size
            request.bug_mgt.project.save()
        # 在数据库中删除文件
        delete_object.delete()
        return JsonResponse({'status': True})


def cos_credential(request, project_id):
    """获取临时凭证给前台"""
    data_dict = credential(request.bug_mgt.project.bucket, request.bug_mgt.project.region)
    return JsonResponse(data_dict)
