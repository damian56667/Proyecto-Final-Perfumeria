# core/templatetags/math_extras.py
from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Resta arg de value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return value

@register.filter
def abs_value(value):
    """Valor absoluto"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value