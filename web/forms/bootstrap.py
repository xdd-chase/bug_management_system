class BootStrapForm(object):
    """BootStrap基类，给需要的字段添加class样式"""
    bootstrap_class_exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():  # name代表当前字段的name，fields则代表每个字段后面的对象
            # 这是对所有的字段添加form-control样式，为了以后能对某些特定的字段不添加或者添加其他样式
            # 则可以对name参数做判断，新建一个列表bootstrap_class_exclude，把想要特殊对待的字段放进去
            # 当我们要向这个列表中更新需要的字段时，只要在form里面对应的类里继承此类，然后重写bootstrap_class_exclude列表就可以了
            if name in self.bootstrap_class_exclude:
                # 若字段在此列表中，则继续循环，不走下面两步
                continue
            # 为防止还有原来自带的class属性，我们获取一下，再用占位符添加进去
            old_class = field.widget.attrs.get('class', "")
            print('sss', old_class)
            field.widget.attrs['class'] = '{} form-control'.format(old_class)
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)
