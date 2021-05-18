from django import template
from web import models
from django.urls import reverse

register = template.Library()


@register.simple_tag
def string_just(num):
    if num < 100:
        num = str(num).rjust(3, "0")
    return "#{}".format(num)
