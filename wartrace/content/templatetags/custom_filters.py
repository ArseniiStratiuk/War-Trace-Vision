from django import template
import os
import re

register = template.Library()

@register.filter
def filename(value):
    return os.path.basename(value)

@register.filter
def split(value, arg):
    """Split a string by the specified delimiter"""
    return value.split(arg)

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key"""
    return dictionary.get(key)

@register.filter
def get_list_item(list_obj, index):
    """Get an item from a list using index"""
    try:
        return list_obj[int(index)]
    except (IndexError, ValueError):
        return None

@register.filter
def join(value, arg):
    """Join a list with the specified delimiter"""
    if isinstance(value, list):
        return arg.join(value)
    return value

@register.filter
def truncate(value, length):
    """Truncate a string to the specified length"""
    try:
        length = int(length)
    except ValueError:
        return value
    
    if len(value) <= length:
        return value
    return value[:length] + '...'

@register.filter
def startswith(value, arg):
    """Check if string starts with the argument"""
    if value is None:
        return False
    return value.startswith(arg)

@register.filter
def endswith(value, arg):
    """Check if string ends with the argument"""
    if value is None:
        return False
    return value.endswith(arg)

@register.filter
def filter_by_prefix(files, prefixes):
    """Filter a queryset of files by prefix in filename"""
    prefix_list = prefixes.split(',')
    result = []
    for file in files:
        filename = os.path.basename(file.file.name)
        for prefix in prefix_list:
            if filename.startswith(prefix.strip()):
                result.append(file)
                break
    return result

@register.filter
def filter_by_prefix_exclusion(queryset, prefixes):
    """Filter a queryset by excluding items whose file.name starts with any of the given prefixes"""
    if not queryset or not prefixes:
        return queryset
    
    # Split multiple prefixes by comma
    prefix_list = [p.strip() for p in prefixes.split(',')]
    
    # Create a filtered list excluding items that start with any prefix
    filtered = []
    for item in queryset:
        filename = item.file.name.split('/')[-1]
        if not any(filename.startswith(prefix) for prefix in prefix_list):
            filtered.append(item)
    
    return filtered
