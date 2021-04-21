from web.forms.bootstrap import BootStrapForm
from django.core.exceptions import ValidationError
from django import forms
from web import models
from utils.tencent.cos import check_file


class FolderModelForm(BootStrapForm, forms.ModelForm):
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


class FileModelForm(forms.ModelForm):
    etag = forms.CharField(label='etag')

    class Meta:
        model = models.FileRepository
        exclude = ['project', 'file_type', 'update_user', 'update_time']  # 忽略掉不用校验的参数

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_file_path(self):
        return "https://{}".format(self.cleaned_data['file_path'])

    def clean(self):
        # 最后执行的校验（即校验etag）
        etag = self.cleaned_data['etag']
        key = self.cleaned_data['key']
        size = self.cleaned_data['size']
        if not etag or not key:
            return self.cleaned_data
        # 向COS校验文件是否合法（因为一个文件只有唯一的etag）
        # 调用sdk接口
        from qcloud_cos.cos_exception import CosServiceError
        try:
            result = check_file(self.request.bug_mgt.project.bucket, self.request.bug_mgt.project.region, key)
            print(result)
        except CosServiceError as e:
            self.add_error(key, '文件上传失败')
            return self.cleaned_data
        # 当检验文件成功，则拿到cos中的文件ETag, 和前台发过来的etag作比较
        cos_etag = result.get('ETag')
        print(cos_etag)
        print(etag)
        if etag != cos_etag:
            self.add_error('etag', "ETag错误")
        cos_length = result.get('Content-Length')
        if int(cos_length) != size:
            self.add_error('size', "文件大小错误")
        return self.cleaned_data
