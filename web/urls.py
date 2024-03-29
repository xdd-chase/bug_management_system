"""bug_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from web.views import account
from web.views import home
from web.views import project, statistics, wiki, file, setting, issues, dashboard

urlpatterns = [
    path('register/', account.register, name='register'),  # name设置便于反向解析
    path('login/sms/', account.login_sms, name='login_sms'),  # 短信验证登录
    path('login/', account.login, name='login'),  # 用户密码验证登录
    path('image/code/', account.image_code, name='image_code'),  # 获取验证码
    path('send/sms/', account.send_sms, name='send_sms'),  # 发送短信
    path('logout/', account.logout, name='logout'),  # 退出
    path('index/', home.index, name='index'),  # 主页
    path('prices/', home.prices, name='prices'),  # 报价
    path('prices/<int:policy_id>/', home.payment, name='payment'),  # 支付页面
    path('prices/pay/', home.pay, name='pay'),  # 支付
    path('prices/pay/notify/', home.notify, name='notify'),  # 支付成功后跳转的页面
    # 项目管理
    path('project/project_list/', project.project_list, name='project_list'),  # 管理中心中的项目列表
    # /project/star/my/1
    # /project/star/join/1
    path('project/star/<str:project_type>/<int:project_id>/', project.project_star, name='project_star'),  # 星标项目
    # 取消星标项目
    path('project/unstar/<str:project_type>/<int:project_id>/', project.project_unstar, name='project_unstar'),

    path('manage/<int:project_id>/', include([
        path('files/', file.file, name='files'),
        path('files/delete/', file.file_delete, name='file_delete'),
        path('cos/credential/', file.cos_credential, name='cos_credential'),
        path('files/post/', file.file_post, name='file_post'),
        path('files/download/<int:file_id>', file.file_download, name='file_download'),

        path('wiki/', wiki.wiki, name='wiki'),
        path('wiki/add', wiki.wiki_add, name='wiki_add'),
        path('wiki/delete/<int:wiki_id>', wiki.wiki_delete, name='wiki_delete'),
        path('wiki/wiki_edit/<int:wiki_id>', wiki.wiki_edit, name='wiki_edit'),
        path('wiki/wiki_upload/', wiki.wiki_upload, name='wiki_upload'),
        path('wiki/catalog', wiki.wiki_catalog, name='wiki_catalog'),
        path('setting/', setting.setting, name='setting'),
        path('setting/delete/', setting.delete, name='setting_delete'),
        path('issues/', issues.issues, name='issues'),
        path('issues/detail/<int:issue_id>', issues.issue_detail, name='issue_detail'),
        path('issues/record/<int:issue_id>', issues.issue_record, name='issue_record'),
        path('issues/change/<int:issue_id>', issues.issue_change, name='issue_change'),
        path('issues/invite/url/', issues.invite_url, name='invite_url'),
        # 概览
        path('dashboard/', dashboard.dashboard, name='dashboard'),
        path('dashboard/issues/chart/', dashboard.issues_chart, name='issues_chart'),
        path('statistics/', statistics.statistics, name='statistics'),
        path('statistics/priority/', statistics.priority_statistics, name='priority_statistics'),
        path('statistics/project_user/', statistics.project_user_statistics, name='project_user_statistics'),

    ])),
    # 邀请链接需要写在外部，不用对用户进行判断就能进入这个页面
    path('invite/url/<str:code>', issues.invite_join, name='invite_join'),

]
