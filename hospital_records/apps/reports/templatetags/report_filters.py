# hospital_records/apps/reports/templatetags/report_filters.py
from django import template
import json

register = template.Library()

@register.filter
def is_list(value):
    """Check if value is a list"""
    return isinstance(value, list)

@register.filter
def is_dict(value):
    """Check if value is a dictionary"""
    return isinstance(value, dict)

@register.filter
def replace(value, arg):
    """Replace characters in string
    Usage: {{ value|replace:"_ " }} replaces underscores with spaces
    """
    try:
        old, new = arg.split(' ')
        return str(value).replace(old, new)
    except:
        return value

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    try:
        return dictionary.get(key)
    except:
        return None

@register.filter
def json_loads(value):
    """Load JSON string"""
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except:
        return {}

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if total and total > 0:
            return f"{(value / total * 100):.1f}%"
        return "0%"
    except:
        return "0%"

@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except:
        return 0

@register.filter
def divide(value, arg):
    """Divide value by argument"""
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except:
        return 0

@register.filter
def truncate(value, length):
    """Truncate string to length"""
    try:
        if len(value) > length:
            return value[:length] + "..."
        return value
    except:
        return value

@register.filter
def format_currency(value):
    """Format as currency"""
    try:
        return f"${float(value):,.2f}"
    except:
        return "$0.00"

@register.filter
def format_number(value):
    """Format number with commas"""
    try:
        return f"{int(value):,}"
    except:
        return value