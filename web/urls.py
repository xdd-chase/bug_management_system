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
from web.views import project, manage, wiki

urlpatterns = [
    path('register/', account.register, name='register'),  # name设置便于反向解析
    path('login/sms/', account.login_sms, name='login_sms'),  # 短信验证登录
    path('login/', account.login, name='login'),  # 用户密码验证登录
    path('image/code/', account.image_code, name='image_code'),  # 获取验证码
    path('send/sms/', account.send_sms, name='send_sms'),  # 发送短信
    path('logout/', account.logout, name='logout'),  # 退出
    path('index/', home.index, name='index'),  # 主页
    # 项目管理
    path('project/project_list/', project.project_list, name='project_list'),  # 管理中心中的项目列表
    # /project/star/my/1
    # /project/star/join/1
    path('project/star/<str:project_type>/<int:project_id>/', project.project_star, name='project_star'),  # 星标项目
    # 取消星标项目
    path('project/unstar/<str:project_type>/<int:project_id>/', project.project_unstar, name='project_unstar'),

    path('manage/<int:project_id>/', include([
        path('dashboard/', manage.dashboard, name='dashboard'),
        path('issues/', manage.issues, name='issues'),
        path('statistics/', manage.statistics, name='statistics'),
        path('file/', manage.file, name='file'),
        path('wiki/', wiki.wiki, name='wiki'),
        path('wiki/add', wiki.wiki_add, name='wiki_add'),
        path('wiki/delete/<int:wiki_id>', wiki.wiki_delete, name='wiki_delete'),
        path('wiki/wiki_edit/<int:wiki_id>', wiki.wiki_edit, name='wiki_edit'),
        path('wiki/catalog', wiki.wiki_catalog, name='wiki_catalog'),
        path('setting/', manage.setting, name='setting'),
    ])),

]
