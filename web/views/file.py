import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from web import models
from web.forms.file import FolderModelForm, FileModelForm
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
        form = FolderModelForm(request, parent_object)
        context = {
            'form': form,
            'file_object_list': file_object_list,
            'breadcrumb_list': breadcrumb_list,
            'folder_object': parent_object
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
        form = FolderModelForm(request, parent_object, data=request.POST, instance=edit_object)
    else:
        # 不存在则为添加文件夹
        form = FolderModelForm(request, parent_object, data=request.POST)
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


@csrf_exempt
def cos_credential(request, project_id):
    """获取临时凭证给前台"""
    # 后台接收参数使用json.loads(request.body.decode('utf-8'))
    file_list = json.loads(request.body.decode('utf-8'))
    per_file_limit = request.bug_mgt.price_policy.per_file_size * 1024 * 1024
    total_size = 0
    for item in file_list:
        # 单文件大小限制
        if item['size'] > per_file_limit:
            msg = "单文件大小超出限制(最大{}M), 文件：{}".format(request.bug_mgt.price_policy.per_file_size, item['name'])
            return JsonResponse({'status': False, 'error': msg})
        total_size += item['size']
    # 总容量进行限制
    if total_size > (request.bug_mgt.price_policy.project_space - request.bug_mgt.project.used_space) * 1024 * 1024:
        return JsonResponse({'status': False, 'error': '超出总容量限制，请升级套餐'})
        print(file_list)
    data_dict = credential(request.bug_mgt.project.bucket, request.bug_mgt.project.region)
    return JsonResponse({'status': True, 'data': data_dict}, safe=False)


@csrf_exempt
def file_post(request, project_id):
    """
    已上传成功的文件写入数据库
    传入的数据参数：
    name: fileName,
    key: key,
    file_size: fileSize,
    parent: CURRENT_FOLDER_ID,
    file_path: data.Location
    """
    print(request.POST)
    form = FileModelForm(request, data=request.POST)
    print(form)
    if form.is_valid():
        # 校验通过，数据写入到数据库
        # 通过 ModelForm.save存储到数据库中的数据返回的instance对象，无法通过get_xxx_display获取到choice中文
        # form.instance.file_type = 1
        # form.update_user = request.bug_mgt.user
        # instance = form.save()  # 添加成功后，可以获取instance.id, instance.name等，但是无法获取instance.file_type的中文

        data_dict = form.cleaned_data
        print(data_dict)
        data_dict.pop('etag')
        data_dict.update({'project': request.bug_mgt.project, 'file_type': 1, 'update_user': request.bug_mgt.user})
        instance = models.FileRepository.objects.create(**data_dict)
        # 项目已使用空间
        request.bug_mgt.project.used_space += data_dict['size']
        request.bug_mgt.project.save()
        print(request.bug_mgt.project.used_space)
        result = {
            'id': instance.id,
            'name': instance.file_name,
            'file_size': instance.size,
            'update_user': instance.update_user.username,
            'datetime': instance.update_time.strftime("%Y{}%m{}%d{} %H:%M").format('年', '月', '日'),
            'file_type': instance.get_file_type_display()
        }
        return JsonResponse({'status': True, 'data': result})

    return JsonResponse({'status': False, 'data': '文件错误'})
