from django import template

register = template.Library()

# custom_filters.py
@register.filter
def resource_class(value):
    if '/' in value:
        value = value.split('/')[-1]  # extrait 'png' de 'image/png'
    value = value.lower().strip()
    if value in ['png', 'jpg', 'jpeg']:
        return 'image'
    elif value == 'pdf':
        return 'pdf'
    elif value in ['mp4', 'mov', 'avi']:
        return 'video'
    elif value in ['mp3', 'wav']:
        return 'audio'
    else:
        return 'other'

