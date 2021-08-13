from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from web import models
from web.forms.wiki import WikiModelForm
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from utils.tencent import cos
from utils.encrypt import uid


def wiki(request, project_id):
    """
    wiki首页
    :param request:
    :param project_id:
    :return:
    """
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, 'web/wiki.html')
    else:
        wiki_object = models.Wiki.objects.filter(id=wiki_id, project_id=project_id).first()
        print(wiki_object.content)
        return render(request, 'web/wiki.html', {'wiki_object': wiki_object})


def wiki_add(request, project_id):
    """
    wiki添加
    :param request:
    :param project_id:
    :return:
    """
    if request.method == 'GET':
        form = WikiModelForm(request)
        return render(request, 'web/wiki_form.html', {'form': form})
    if request.method == 'POST':
        form = WikiModelForm(request, data=request.POST)
        if form.is_valid():
            # 判断是否选择父级文章，如果选择，则depth+1,如果没选择，则forms.instance.depth=1
            if form.instance.parent:
                form.instance.depth = form.instance.parent.depth + 1
            else:
                form.instance.depth = 1
            form.instance.project = request.bug_mgt.project
            form.save()
            url = reverse('wiki', kwargs={'project_id': project_id})
            return redirect(url)
        return render(request, 'web/wiki_form.html', {'form': form})


def wiki_delete(request, project_id, wiki_id):
    """删除wiki"""
    models.Wiki.objects.filter(id=wiki_id, project_id=project_id).delete()
    url = reverse('wiki', kwargs={'project_id': project_id})
    return redirect(url)


def wiki_edit(request, project_id, wiki_id):
    """编辑Wiki"""
    # 判断是否存在此编辑对象，不存在则返回到Wiki页面
    wiki_object = models.Wiki.objects.filter(project_id=project_id, id=wiki_id).first()
    if not wiki_object:
        url = reverse('wiki', kwargs={'project_id': project_id})
        return redirect(url)
    # 和wiki_add一样，先出现form表单，表单中有默认值
    if request.method == 'GET':
        form = WikiModelForm(request, instance=wiki_object)
        return render(request, 'web/wiki_form.html', {'form': form})
    form = WikiModelForm(request, data=request.POST, instance=wiki_object)
    if form.is_valid():
        # 判断是否选择父级文章，如果选择，则depth+1,如果没选择，则forms.instance.depth=1
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.save()
        url = reverse('wiki', kwargs={'project_id': project_id})
        # 给他重新定位到当前Wiki的页面
        preview_url = "{0}?wiki_id={1}".format(url, wiki_id)
        return redirect(preview_url)
    return render(request, 'web/wiki_form.html', {'form': form})


@csrf_exempt
def wiki_upload(request, project_id):
    """markdown插件上传图片"""
    file_project = request.FILES.get('editormd-image-files')
    if not file_project:
        result = {
            'success': 0,  # 0 表示上传失败，1 表示上传成功
            'message': "上传失败",
            'url': None
        }
        return JsonResponse(result)
    ext = file_project.name.rsplit('.')[-1]  # 拿到后缀名
    key = "{}-{}".format(uid(request.bug_mgt.user.mobile_phone), ext)
    # project_obj = models.Project.objects.filter(id=project_id).first() 或 request.bug_mgt.project.bucket
    bucket = request.bug_mgt.project.bucket
    region = request.bug_mgt.project.region
    file_url = cos.upload_file(bucket, file_project, region, key)
    print(file_url)
    result = {
        'success': 1,  # 0 表示上传失败，1 表示上传成功
        'message': "上传成功",
        'url': file_url  # 上传成功时才返回
    }
    # 返回一个路径
    return JsonResponse(result)


def wiki_catalog(request, project_id):
    """wiki目录"""
    data = models.Wiki.objects.filter(project_id=project_id).values('id', 'title', 'parent_id').order_by('depth', 'id')
    # 数据库查询出来的data是queryset类型，不能序列化为json 格式，先list一下
    data = list(data)
    return JsonResponse({'status': True, 'data': data})
