from django.db import models


# Create your models here.
class UserInfo(models.Model):
    username = models.CharField(verbose_name='用户名', max_length=64, db_index=True)  # db_index=True创建索引，查询更快
    email = models.EmailField(verbose_name='邮箱', max_length=64)
    mobile_phone = models.CharField(verbose_name='手机号', max_length=64)
    password = models.CharField(verbose_name='密码', max_length=64)


class PricePolicy(models.Model):
    """价格策略"""
    category_choices = (
        (1, '免费版'),
        (2, '收费版'),
        (3, '其他'),
    )
    category = models.SmallIntegerField(verbose_name='收费类型', choices=category_choices, default=1)
    title = models.CharField(verbose_name='标题', max_length=32)
    price = models.PositiveIntegerField(verbose_name='价格')
    project_num = models.PositiveIntegerField(verbose_name='项目个数')
    project_member = models.PositiveIntegerField(verbose_name='项目成员数')
    project_space = models.PositiveIntegerField(verbose_name='单个项目空间')
    per_file_size = models.PositiveIntegerField(verbose_name='单个文件大小')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Transaction(models.Model):
    """交易记录"""
    status_choice = (
        (1, '未支付'),
        (2, '已支付'),
    )
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choice)
    order = models.CharField(verbose_name='订单号', max_length=64, unique=True)  # unique=True唯一索引
    user = models.ForeignKey(verbose_name='用户', to='UserInfo', on_delete=models.CASCADE)
    price_policy = models.ForeignKey(verbose_name='价格策略', to='PricePolicy', on_delete=models.CASCADE)
    count = models.IntegerField(verbose_name='数量（年）', help_text='0表示无限制')
    price = models.IntegerField(verbose_name='实际支付的价格')
    start_datetime = models.DateTimeField(verbose_name='开始时间', null=True, blank=True)
    end_datetime = models.DateTimeField(verbose_name='结束时间', null=True, blank=True)
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Project(models.Model):
    """项目表"""
    color_choice = (
        (1, '#56b8eb'),
        (2, '#f28033'),
        (3, '#ebc656'),
        (4, '#a2d148'),
        (5, '#208fa4'),
        (6, '#7461c2'),
        (7, '#20bfa3'),
    )
    name = models.CharField(verbose_name='项目名', max_length=64)
    color = models.SmallIntegerField(verbose_name='颜色', choices=color_choice, default=1)
    desc = models.TextField(verbose_name='项目描述', null=True, blank=True)
    used_space = models.IntegerField(verbose_name='项目已使用空间', default=0)
    star = models.BooleanField(verbose_name='星标', default=False)
    join_count = models.SmallIntegerField(verbose_name='项目参与人数', default=1)
    creator = models.ForeignKey(verbose_name='创建者', to='UserInfo', on_delete=models.CASCADE)
    create_datetime = models.DateTimeField(verbose_name='项目创建时间', auto_now_add=True)
    bucket = models.CharField(verbose_name='COS桶', max_length=128)
    region = models.CharField(verbose_name='COS区域', max_length=32)


class ProjectUser(models.Model):
    """项目参与者"""
    user = models.ForeignKey(verbose_name='用户', to='UserInfo', on_delete=models.CASCADE)
    project = models.ForeignKey(verbose_name='项目', to='Project', on_delete=models.CASCADE)
    star = models.BooleanField(verbose_name='星标', default=False)
    create_datetime = models.DateTimeField(verbose_name='加入时间', auto_now_add=True)


class Wiki(models.Model):
    project = models.ForeignKey(verbose_name='项目', to='Project', on_delete=models.CASCADE)
    title = models.CharField(verbose_name='标题', max_length=32)
    content = models.TextField(verbose_name='内容')
    depth = models.IntegerField(verbose_name='深度', default=1)  # 深度，代表目录是第几级目录，每当添加一个子目录，就加一
    # 自关联
    parent = models.ForeignKey(verbose_name='父级文章', to='Wiki', null=True, blank=True, on_delete=models.CASCADE,
                               related_name='children')

    def __str__(self):
        return self.title


class FileRepository(models.Model):
    file_type_choice = (
        (1, '文件'),
        (2, '文件夹')
    )
    project = models.ForeignKey(verbose_name='项目', to='Project', on_delete=models.CASCADE)
    file_name = models.CharField(verbose_name='文件或文件夹名', max_length=64)
    file_type = models.SmallIntegerField(verbose_name='类型', choices=file_type_choice)
    size = models.FloatField(verbose_name='大小', max_length=128, null=True)
    parent = models.ForeignKey(verbose_name='父目录', to='FileRepository', null=True, blank=True, on_delete=models.CASCADE)
    key = models.CharField(verbose_name='唯一文件名称', max_length=128, null=True,
                           blank=True, )  # 当上传同名文件时，我们允许创建，给他设置一个key,来区分
    file_path = models.CharField(verbose_name='文件路径', max_length=256, null=True, blank=True)
    update_user = models.ForeignKey(verbose_name='更新者', to='UserInfo', on_delete=models.CASCADE)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
