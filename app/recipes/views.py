from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.core.paginator import Paginator
from django.utils.http import urlencode

import re
import pandas as pd

from .models import Recipe, Rating


def index(request):
	base_url = reverse("recipes:browse")

	pop_rec_category = "popular recipes"
	pop_rec_list = Recipe.objects.order_by("-review_count")[:8]
	pop_rec_link = base_url
	pop_rec = {'category': pop_rec_category, 'list': pop_rec_list, 'url': pop_rec_link}

	pizza_category = "pizza party"
	pizza_list = Recipe.objects.filter(name__icontains='pizza').order_by("-review_count")[:8]
	pizza_link = f"{base_url}?{urlencode({'name': 'pizza'})}"
	pizza_rec = {'category': pizza_category, 'list': pizza_list, 'url': pizza_link}

	weeknight_category = "tonight's dinner"
	weeknight_list = Recipe.objects.filter(category='Weeknight').order_by("-review_count")[:8]
	weeknight_link = f"{base_url}?{urlencode({'category': 'Weeknight'})}"
	weeknight_rec = {'category': weeknight_category, 'list': weeknight_list, 'url': weeknight_link}

	return render(request, 'recipes/index.html', {
		'recs': [pop_rec, pizza_rec, weeknight_rec]
	})


def browse(request):
	recipe_list = Recipe.objects.all()
	
	name = request.GET.get('name')
	if name:
		recipe_list = recipe_list.filter(name__icontains=name)

	category = request.GET.get('category')
	if category:
		recipe_list = recipe_list.filter(category=category)

	recipe_list = recipe_list.order_by('-review_count')

	paginator = Paginator(recipe_list, 12)

	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	return render(request, 'recipes/browse.html', {
		'page_obj': page_obj,
		'name': name
	})


def detail(request, recipe_id):
	recipe = get_object_or_404(Recipe, pk = recipe_id)
	ingredients = re.sub(r'(c\()|\)|"', '', recipe.ingredients).split(', ')
	ing_amounts = re.sub(r'(c\()|\)|"', '', recipe.ingredient_quantities).split(', ')
	steps = re.sub(r'(c\()|\)|"', '', recipe.instructions).split(', ')
    
	minutes = re.sub(r'\D', '', recipe.minutes)
	nutrition_labels = ['Calories', 'Total Fat', 'Saturated Fat', 'Cholesterol', 'Sodium', 'Total Carbohydrate', 'Dietary Fiber', 'Sugars', 'Protein']
	nutrition_vals = [recipe.calories, recipe.fat_content, recipe.saturated_fat_content, recipe.cholesterol_content, recipe.sodium_content, recipe.carbohydrates_content, recipe.fiber_content, recipe.sugar_content, recipe.protein_content]
	#Nutrient daily values sourced from the FDA (https://www.fda.gov/food/nutrition-facts-label/daily-value-nutrition-and-supplement-facts-labels)
	nutrition_dv = [2000, 78, 20, 300, 2300, 275, 28, 50, 50]
	nutrition_units = ['', 'g', 'g', 'mg', 'mg', 'g', 'g', 'g', 'g']
	nutrition_pct = [round((val / dv) * 100, 2) for val, dv in zip(nutrition_vals, nutrition_dv)]

	return render(request, 'recipes/detail.html', {
          'recipe': recipe, 
          'ingredients': list(zip(ing_amounts, ingredients)), 
          'n_ingredients': len(ingredients),
					'steps': steps, 
					'minutes': minutes,
          'nutrition_info': list(zip(nutrition_labels, nutrition_vals, nutrition_units, nutrition_pct))
  })	