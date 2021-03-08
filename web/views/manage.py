from django.shortcuts import render


def dashboard(request, project_id):
    return render(request, 'web/dashboard.html')


def issues(request, project_id):
    return render(request, 'web/issues.html')


def statistics(request, project_id):
    return render(request, 'web/statistics.html')



def setting(request, project_id):
    return render(request, 'web/setting.html')
