from web.forms.bootstrap import BootStrapForm
from django.core.exceptions import ValidationError
from django import forms
from web import models


class FileModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.FileRepository
        fields = ['file_name']

    def __init__(self, request, parent_object, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_object = parent_object

    def clean_file_name(self):
        name = self.cleaned_data['file_name']
        # 数据库判断此文件在当前目录下是否已存在
        queryset = models.FileRepository.objects.filter(file_type=2, file_name=name,
                                                        project=self.request.bug_mgt.project)
        if self.parent_object:
            exists = queryset.filter(parent=self.parent_object).exists()
        else:
            exists = queryset.filter(parent_id__isnull=True).exists()
        if exists:
            raise ValidationError("文件夹已存在")
        return name
