from django import template

register = template.Library()

@register.filter(name='recipe_time')
def recipe_time(minutes):
    return minutes.lstrip('PT').replace('H', 'H ')