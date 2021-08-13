import datetime
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from web.forms.issues import IssuesModelForm, IssuesReplyModelForm, InviteModelForm
from web import models
from utils.pagination import Pagination
from utils.encrypt import uid


class CheckFilter(object):
    def __init__(self, name, data_list, request):
        self.data_list = data_list
        self.request = request
        self.name = name

    def __iter__(self):
        for item in self.data_list:
            key = str(item[0])
            text = item[1]
            ck = ""
            value_list = self.request.GET.getlist(self.name)
            # 如果当前用户url中status和当前循环的key相等
            if key in value_list:
                ck = "checked"
                value_list.remove(key)
            else:
                value_list.append(key)
            # 为自己生成url，在当前的url基础上增加一项
            # status=1&age=2
            query_dict = self.request.GET.copy()
            # 给query_dict设置_mutable属性为True，则能对query_dict进行修改
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)
            if 'page' in query_dict:
                query_dict.pop('page')
            if not query_dict.urlencode():
                url = self.request.path_info
            else:
                url = "{}?{}".format(self.request.path_info, query_dict.urlencode())  # status=1&status=2
            tpl = '<a class="cell" href="{url}"><input type="checkbox" {ck}/><label>{text}</label></a>'
            html = tpl.format(ck=ck, text=text, url=url)
            yield mark_safe(html)


class SelectFilter(object):
    def __init__(self, name, data_list, request):
        self.data_list = data_list
        self.request = request
        self.name = name

    def __iter__(self):
        yield mark_safe("<select class='select2' multiple='multiple' style='width:100%'>")
        for item in self.data_list:
            key = str(item[0])
            text = item[1]
            selected = ''
            value_list = self.request.GET.getlist(self.name)
            print(value_list)
            if key in value_list:
                selected = 'selected'
                value_list.remove(key)
            else:
                value_list.append(key)
            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)
            if 'page' in query_dict:
                query_dict.pop('page')
            if not query_dict.urlencode():
                url = self.request.path_info
            else:
                url = "{}?{}".format(self.request.path_info, query_dict.urlencode())  # status=1&status=2
            html = "<option value='{url}' {selected}>{text}</option>".format(url=url, selected=selected, text=text)
        yield mark_safe(html)
        yield mark_safe("</select>")


def issues(request, project_id):
    if request.method == "GET":
        # 筛选条件
        # ？status=1&issue_type=2
        allow_filter_name = ['issues_type', 'status', 'priority', 'assign', 'attention']
        condition = {}
        for name in allow_filter_name:
            value_list = request.GET.getlist(name)
            if not value_list:
                continue
            condition["{}__in".format(name)] = value_list
        """
        condition = {
            "status__in": [1,2],
            "issues_type__in": [1,]
        }
        """
        # 分页获取数据
        queryset = models.Issues.objects.filter(project_id=project_id).filter(**condition)
        page_object = Pagination(
            current_page=request.GET.get('page'),
            all_count=queryset.count(),
            base_url=request.path_info,
            query_params=request.GET,
            per_page=1
        )
        issues_object_list = queryset[page_object.start:page_object.end]
        form = IssuesModelForm(request)
        issues_type_list = models.IssuesType.objects.filter(project_id=project_id).values_list('id', 'title')

        project_total_user = [(request.bug_mgt.project.creator_id, request.bug_mgt.project.creator.username)]
        project_join_user = models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id',
                                                                                                 'user__username')
        project_total_user.extend(project_join_user)

        invite_form = InviteModelForm()
        context = {
            'form': form,
            'invite_form': invite_form,
            'issues_object_list': issues_object_list,
            'page_html': page_object.page_html(),
            'filter_list': [
                {'title': '问题类型', 'filter': CheckFilter('issues_type', issues_type_list, request)},
                {'title': '状态', 'filter': CheckFilter('status', models.Issues.status_choices, request)},
                {'title': '优先级', 'filter': CheckFilter('priority', models.Issues.priority_choices, request)},
                {'title': '指派者', 'filter': SelectFilter('assign', project_total_user, request)},
                {'title': '关注者', 'filter': SelectFilter('attention', project_total_user, request)},
            ]
        }
        return render(request, 'web/issues.html', context)
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


@csrf_exempt
def issue_change(request, project_id, issue_id):
    post_dict = json.loads(request.body.decode('utf-8'))
    print(post_dict)
    property_name = post_dict.get('name')
    property_value = post_dict.get('value')
    issues_object = models.Issues.objects.filter(project_id=project_id, id=issue_id).first()
    # 获取issues表中某个字段的属性，例如verbose_name
    filed_objects = models.Issues._meta.get_field(property_name)

    def create_reply_record(content):
        new_object = models.IssuesReply.objects.create(
            reply_type=1,
            issue=issues_object,
            content=content,
            creator=request.bug_mgt.user
        )
        data = {
            'id': new_object.id,
            'reply_type': new_object.get_reply_type_display(),
            'content': new_object.content,
            'creator': new_object.creator.username,
            'datetime': new_object.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id': new_object.reply_id

        }
        return data

    # 1.数据库更新
    #  1.1文本字段处理
    if property_name in ['subject', 'desc', 'start_date', 'end_date']:
        if not property_value:
            if not filed_objects.null:
                return JsonResponse({'status': False, 'error': '你选择的值不能为空'})
            setattr(issues_object, property_name, None)
            issues_object.save()
            # 生成一条更新记录
            change_record = '{}更新为空'.format(filed_objects.verbose_name)
        else:
            setattr(issues_object, property_name, property_value)
            issues_object.save()
            # 生成一条更新记录
            change_record = '{}更新为{}'.format(filed_objects.verbose_name, property_value)
        return JsonResponse({'status': True, 'data': create_reply_record(change_record)})
    # 1.2FK字段处理
    if property_name in ['issues_type', 'module', 'assign', 'parent']:
        # 用户选择为空
        print('11', filed_objects.null)
        if not property_value:
            # 不允许为空
            if not filed_objects.null:
                return JsonResponse({'status': False, 'error': '你选择的值不能为空'})
            # 允许为空
            setattr(issues_object, property_name, None)
            issues_object.save()
            change_record = '{}更新为空'.format(filed_objects.verbose_name)
        else:  # 用户选择的不为空
            if property_name == 'assign':
                # 对FK处理中，对指派的人员要独立判断
                # 是否是创建者
                if property_value == str(request.bug_mgt.project.creator_id):
                    instance = request.bug_mgt.project.creator
                else:
                    # 是否是项目参与者
                    project_user_object = models.ProjectUser.objects.filter(project_id=project_id,
                                                                            user_id=property_value).first()
                    if project_user_object:
                        instance = project_user_object.user
                    else:
                        instance = None
                if not instance:
                    return JsonResponse({'status': False, 'error': '你选择的值不存在'})
                setattr(issues_object, property_name, instance)
                issues_object.save()
                change_record = '{}更新为{}'.format(filed_objects.verbose_name, str(instance))
            else:
                # 当用户选择的值存在时，此时需要检查选择的值在当前这个问题所关联的表中是否有对应的值，否则就是非法输入，所以需要查询一下
                instance = filed_objects.remote_field.model.objects.filter(id=property_value,
                                                                           project_id=project_id).first()
                if not instance:
                    return JsonResponse({'status': False, 'error': '你选择的值不存在'})
                setattr(issues_object, property_name, instance)
                issues_object.save()
                change_record = '{}更新为{}'.format(filed_objects.verbose_name, str(instance))

        return JsonResponse({'status': True, 'data': create_reply_record(change_record)})
    # 1.3choices处理
    if property_name in ['priority', 'status', 'mode']:
        selected_text = None
        for key, text in filed_objects.choices:
            if property_value == str(key):
                selected_text = text
        if not selected_text:
            return JsonResponse({'status': False, 'error': '你选择的值不存在'})
        setattr(issues_object, property_name, property_value)
        issues_object.save()
        # 生成一条更新记录
        change_record = '{}更新为{}'.format(filed_objects.verbose_name, selected_text)
        return JsonResponse({'status': True, 'data': create_reply_record(change_record)})
    # 1.4M2M字段
    if property_name == 'attention':
        # {'name':"attention", 'value': [1,2,3]}
        if not isinstance(property_value, list):  # 判断value 是否是list实例
            return JsonResponse({'status': False, 'error': '数据格式错误'})
        if not property_value:  # 如果关注者为空
            issues_object.attention.set([])
            issues_object.save()
            change_record = '{}更新为空'.format(filed_objects.verbose_name)
        else:
            # 若不为空，则对传过来的成员id列条进行校验，是否是当前项目的项目成员（参与者和创建者）
            # 获取当前项目的所有项目成员
            user_dict = {str(request.bug_mgt.project.creator_id): request.bug_mgt.project.creator.username}
            project_user_dict = models.ProjectUser.objects.filter(project_id=project_id)
            for item in project_user_dict:
                user_dict[str(item.user_id)] = item.user.username
            username_list = []
            for user_id in property_value:
                username = user_dict.get(str(user_id))
                if not username:  # 若不是项目成员，则报错
                    return JsonResponse({'status': False, 'error': '数据错误，请刷新再操作'})
                username_list.append(username)
            issues_object.attention.set(property_value)
            issues_object.save()
            change_record = '{}更新为{}'.format(filed_objects.verbose_name, ",".join(username_list))
        return JsonResponse({'status': True, 'data': create_reply_record(change_record)})
    return JsonResponse({'status': False, 'error': '数据错误'})


def invite_url(request, project_id):
    """生成邀请码"""
    form = InviteModelForm(data=request.POST)
    if form.is_valid():
        """
        1.创建随机的邀请码
        2.验证码保存到数据库
        3.限制：只有项目创建者才能邀请
        """
        if request.bug_mgt.user != request.bug_mgt.project.creator:
            form.add_error('period', "无权创建邀请码")
            return JsonResponse({'status': False, 'error': form.errors})
        else:
            # 生成邀请码并保存到数据库
            random_invite_code = uid(request.bug_mgt.user.mobile_phone)
            form.instance.project = request.bug_mgt.project
            form.instance.code = random_invite_code
            form.instance.creator = request.bug_mgt.user
            form.save()
            # 将邀请码返回给前端，前端页面展示出来
            # 通过reverse方法生成路径：invite/join/code/
            url_path = reverse('invite_join', kwargs={'code': random_invite_code})
            url = "{scheme}://{host}{path}".format(
                scheme=request.scheme,
                host=request.get_host(),
                path=url_path
            )
            return JsonResponse({'status': True, 'data': url})
    return JsonResponse({'status': False, 'error': form.errors})


def invite_join(request, code):
    """访问邀请码"""
    current_date = datetime.datetime.now()
    invite_project = models.ProjectInvite.objects.filter(code=code).first()
    # 判断邀请码是否存在
    if not invite_project:
        return render(request, 'web/invite_join.html', {'error': '邀请码不存在'})
    # 判断是否是项目创建者，创建者不需要加入项目
    if invite_project.project.creator == request.bug_mgt.user:
        return render(request, 'web/invite_join.html', {'error': '创建者无需再加入项目'})
    # 判断用户是否加入此项目
    exists = models.ProjectUser.objects.filter(project=invite_project.project, user=request.bug_mgt.user).exists()
    if exists:
        return render(request, 'web/invite_join.html', {'error': '已加入项目，无需再加入'})
    # 允许最多的成员(要进入的项目的创建者的限制)
    # 判断要进入的那个项目的额度（是免费额度还是收费版额度）,通过order_by('-id')查到最大的额度
    max_transaction = models.Transaction.objects.filter(user=invite_project.project.creator).order_by('-id').first()
    if max_transaction.price_policy.category == 1:
        max_member = max_transaction.price_policy.project_member
    else:
        # 判断当前套餐是否过期, 若过期，则使用免费额度
        if max_transaction.end_datetime < current_date:
            free_object = models.PricePolicy.objects.filter(category=1).first()
            max_member = free_object.project_member
        else:
            max_member = max_transaction.price_policy.project_member

    # 目前项目所有成员（创建者和参与者）
    current_member = models.ProjectUser.objects.filter(project=invite_project.project).count()
    current_member = current_member + 1
    if current_member >= max_member:
        return render(request, 'web/invite_join.html', {'error': '项目成员已超限，请购买套餐'})
    # 邀请码是否过期
    limit_time = invite_project.create_datetime + datetime.timedelta(minutes=invite_project.period)
    if current_date > limit_time:
        return render(request, 'web/invite_join.html', {'error': '验证码已过期'})
    # 数量限制
    if invite_project.count:
        if invite_project.use_count >= invite_project.count:
            return render(request, 'web/invite_join.html', {'error': '邀请码数量已用完'})
        else:
            invite_project.use_count += 1
            invite_project.save()
    # 所有判断验证完成后，将此被邀请者加入到项目成员中
    models.ProjectUser.objects.create(user=request.bug_mgt.user, project=invite_project.project)
    return render(request, 'web/invite_join.html', {'project': invite_project.project})
