from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from web import models
from web.forms.wiki import WikiModelForm
from django.urls import reverse


def wiki(request, project_id):
    """
    wiki首页
    :param request:
    :param project_id:
    :return:
    """
    wiki_id = request.GET.get('wiki_id')
    if wiki_id:
        print('文章详情')
    else:
        print('文章首页')

    return render(request, 'web/wiki.html')


def wiki_add(request, project_id):
    """
    wiki添加
    :param request:
    :param project_id:
    :return:
    """
    if request.method == 'GET':
        form = WikiModelForm(request)
        return render(request, 'web/wiki_add.html', {'form': form})
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
        return render(request, 'web/wiki_add.html', {'form': form})


def wiki_catalog(request, project_id):
    """wiki目录"""
    data = models.Wiki.objects.filter(project_id=project_id).values('id', 'title', 'parent_id').order_by('depth', 'id')
    # 数据库查询出来的data是queryset类型，不能序列化为json 格式，先list一下
    data = list(data)
    return JsonResponse({'status': True, 'data': data})

