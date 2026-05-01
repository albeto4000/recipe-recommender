from django import template
register = template.Library()

@register.filter
def negate(value):
    try:
        return -value
    except (TypeError, ValueError):
        return value
