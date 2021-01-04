from django import forms
from web.forms.bootstrap import BootStrapForm
from web import models
from django.core.exceptions import ValidationError
from web.forms.widgets import ColorRadioSelect


class ProjectModelForm(BootStrapForm, forms.ModelForm):
    # 如果想改变前台form表单中的desc显示的属性。则可以重写这个字段,给字段添加widget属性，改成你想要的
    # desc = forms.CharField(widget=forms.TextInput())
    # 还有一种方法，直接在Meta中设置widjets属性
    bootstrap_class_exclude = ['color']

    class Meta:
        model = models. Project
        fields = ['name', 'color', 'desc']
        # widgets = {'desc': forms.TextInput}
        widgets = {
            'color': ColorRadioSelect(attrs={'class': 'color-radio'})
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_name(self):
        name = self.cleaned_data['name']
        # 1.当前用户是否创建此项目
        exist = models.Project.objects.filter(name=name, creator=self.request.bug_mgt.user).exists()
        if exist:
            raise ValidationError("项目已存在")
        # 2.当前用户是否有额度创建项目
        count = models.Project.objects.filter(creator=self.request.bug_mgt.user).count()
        if count >= self.request.bug_mgt.price_policy.project_num:
            raise ValidationError("项目个数超限，请购买套餐")
        return name
