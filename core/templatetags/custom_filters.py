# core/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Resta arg de value"""
    try:
        result = float(value) - float(arg)
        return round(result, 2)
    except (ValueError, TypeError):
        return value

@register.filter
def calcular_ahorro(precio, descuento):
    """Calcula el monto ahorrado"""
    try:
        precio = float(precio)
        desc = float(descuento)
        
        # Si descuento es como 0.20 (20%)
        if desc < 1:
            return round(precio * desc, 2)
        else:  # Si es como 20 (porcentaje)
            return round(precio * (desc/100), 2)
    except (ValueError, TypeError):
        return 0
    

    from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value