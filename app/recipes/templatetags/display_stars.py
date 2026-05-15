from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def stars(n_stars, frac, total):
	if n_stars > 0:
		solid_star_html = "<i class='fa-solid fa-star text-warning'></i>"
		empty_star_html = "<i class='fa-regular fa-star text-warning'></i>"
		
		stars = solid_star_html * int(n_stars)

		if frac and (float(n_stars) != int(n_stars)):
			stars += '<i class="fa-solid fa-star-half text-warning"></i>'
		if total:
			stars += empty_star_html * (5 - int(n_stars))
		
		return mark_safe(stars)
	else:
		return ""
