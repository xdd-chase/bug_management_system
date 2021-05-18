from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from web.forms.issues import IssuesModelForm, IssuesReplyModelForm
from web import models
from utils.pagination import Pagination


def issues(request, project_id):
    if request.method == "GET":
        # 分页获取数据
        queryset = models.Issues.objects.filter(project_id=project_id)
        page_object = Pagination(
            current_page=request.GET.get('page'),
            all_count=queryset.count(),
            base_url=request.path_info,
            query_params=request.GET,
            per_page=1
        )
        issues_object_list = queryset[page_object.start:page_object.end]
        form = IssuesModelForm(request)
        return render(request, 'web/issues.html',
                      {'form': form, 'issues_object_list': issues_object_list, 'page_html': page_object.page_html()})
    form = IssuesModelForm(request, data=request.POST)
    if form.is_valid():
        # 添加问题
        form.instance.project = request.bug_mgt.project
        form.instance.creator = request.bug_mgt.user
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def issue_detail(request, project_id, issue_id):
    instance = models.Issues.objects.filter(project_id=project_id, id=issue_id).first()
    form = IssuesModelForm(request, instance=instance)
    return render(request, 'web/issue_detail.html', {'form': form, 'issues_object': instance})


@csrf_exempt
def issue_record(request, project_id, issue_id):
    """初始化操作记录"""
    if request.method == 'GET':
        reply_list = models.IssuesReply.objects.filter(issue_id=issue_id, issue__project=request.bug_mgt.project)
        # 将queryset转化为json格式
        data_list = []
        for row in reply_list:
            data = {
                'id': row.id,
                'reply_type': row.get_reply_type_display(),
                'content': row.content,
                'creator': row.creator.username,
                'datetime': row.create_datetime.strftime("%Y-%m-%d %H:%M"),
                'parent_id': row.reply_id

            }
            data_list.append(data)
        return JsonResponse({'status': True, 'data': data_list})
    form = IssuesReplyModelForm(data=request.POST)
    print(form)
    if form.is_valid():
        form.instance.issue_id = issue_id
        form.instance.creator = request.bug_mgt.user
        form.instance.reply_type = 2
        instance = form.save()
        info = {
            'id': instance.id,
            'reply_type': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id': instance.reply_id
        }
        return JsonResponse({'status': True, 'data': info})
    return JsonResponse({'status': False, 'error': form.errors})
