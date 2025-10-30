# templatetags/review_tags.py
from django import template

register = template.Library()

@register.filter
def times(number):
    try:
        return range(int(number))
    except (TypeError, ValueError):
        return range(0)

@register.filter
def subtract(value, arg):
    if value is None:
        value = 0
    if arg is None:
        arg = 0
    return int(value) - int(arg)
