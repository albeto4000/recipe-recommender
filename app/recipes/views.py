from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.core.paginator import Paginator
from django.utils.http import urlencode
from django.core import serializers

import re
import json

from functools import reduce
from operator import or_

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

	spring_category = "flavors of spring"
	spring_list = Recipe.objects.filter(keywords__icontains='spring').order_by("-review_count")[:8]
	spring_link = f"{base_url}?{urlencode({'keywords': 'spring'})}"
	spring_rec = {'category': spring_category, 'list': spring_list, 'url': spring_link}

	return render(request, 'recipes/index.html', {
		'recs': [pop_rec, pizza_rec, weeknight_rec, spring_rec]
	})


def browse(request):
	recipe_list = Recipe.objects.all()

	query = Q()
	
	name = request.GET.get('name')
	if name:
		query &= Q(name__icontains=name)

	category = request.GET.get('category')
	if category:
		query &= Q(category=category)

	keywords = request.GET.get('keywords')
	if keywords:
		query &= Q(keywords__icontains=keywords)

	recipe_list = Recipe.objects.filter(query).order_by('-review_count')

	paginator = Paginator(recipe_list, 12)

	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	return render(request, 'recipes/browse.html', {
		'page_obj': page_obj
	})


def detail(request, recipe_id):
	recipe = get_object_or_404(Recipe, pk = recipe_id)
	ingredients = re.sub(r'(c\()|\)|"', '', recipe.ingredients).split(', ')
	#recipes.ingredients.lstrip('[').rstrip(']').split(', ')
	ing_amounts = re.sub(r'(c\()|\)|"', '', recipe.ingredient_quantities).split(', ')
	#ing_amounts = recipes.ingredient_quantities.split()
	steps = re.sub(r'(c\()|\)|"', '', recipe.instructions).split(', ')
	#
    
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


def search(request):
	recipe_list = Recipe.objects.all().order_by('-review_count')

	paginator = Paginator(recipe_list, 12)

	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	
	season_filter = {
		'category': 'season', 
		'choices': [
			('spring', 'spring'), 
			('summer', 'summer'), 
			('fall', 'fall'), 
			('winter', 'winter')], 
		'filters': 'keywords'
	}

	seafood = ['bass', 'catfish', 'crab', 'crawfish', 'fish halibut', 
	'lobster', 'mahi mahi', 'mussels', 'no shell fish', 'octopus', 
	'oysters', 'squid', 'tilapia', 'trout', 'tuna', 'whitefish']

	protein_filter = {
		'category': 'protein', 
		'choices': [
			('beef', 'beef'), 
			('chicken', 'chicken'), 
			('pork', 'pork|ham'), 
			('turkey', 'turkey'),
			('seafood', '|'.join(seafood))
		], 
		'filters': 'keywords'
	}

	diet_filter = {
		'category': 'Dietary Need',
		'choices': [
			('egg free', 'egg free'),
			('kosher', 'kosher'),
			('healthy', 'healthy'),
			('high fiber', 'high fiber'),
			('lactose free', 'dairy free foods|lactose free'),
			('low carbs', 'very low carbs'),
			('low cholesterol', 'low cholesterol'),
			('low protein', 'low protein'),
			('vegan', 'vegan')
		],
		'filters': 'keywords'
	}

	cook_time_filter = {
		'category': 'Cook Time',
		'choices': [
			('< 15 Mins', '< 15 Mins'),
			('< 30 Mins', '< 30 Mins'),
			('< 60 Mins', '< 60 Mins'),
			('< 4 Hours', '< 4 Hours')
		],
		'filters': 'keywords'
	}

#* Kid Friendly
#* Toddler Friendly

	return render(request, 'recipes/search.html', {
		'filters': [season_filter, protein_filter, diet_filter, cook_time_filter],
		'page_obj': page_obj
	})


def query(request):
	recipe_list = Recipe.objects.all()

	query = Q()

	res = json.loads(request.body)

	for filter_col, filter_val in zip(res['filter_col'], res['filter_val']):
		if filter_col == 'keywords':
			values = filter_val.split('|')
			keyword_query = reduce(
				or_,
				(Q(keywords__icontains = v) for v in values)
			)
			query &= keyword_query
		elif filter_col == 'category':
			query &= Q(category__in=filter_val)
		elif filter_col == 'name':
			query &= Q(name__icontains=filter_val)

	recipe_list = Recipe.objects.filter(query).order_by('-review_count')

	paginator = Paginator(recipe_list, 12)

	page_number = res['page']
	print(page_number)
	page_obj = paginator.get_page(page_number)

	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return render(request, 'recipes/paginated-recipes.html', {
			'page_obj': page_obj,
			'filters_selected': res['filter_label']
	})
