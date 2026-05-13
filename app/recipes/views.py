from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.core.paginator import Paginator

import re
import pandas as pd

from .models import Recipe, Rating


def index(request):
 pop_rec_category = "popular recipes"
 pop_rec_list = Recipe.objects.order_by("-review_count")[:8]
 pop_rec_link = 'recipes:browse'

 pop_rec = {'category': pop_rec_category, 'list': pop_rec_list, 'url': pop_rec_link}

 rate_rec_category = "highly rated"
 rate_rec_list = Recipe.objects.order_by("-aggregated_rating")[:8]
 rate_rec_link = "recipes:browse"

 rate_rec = {'category': rate_rec_category, 'list': rate_rec_list, 'url': rate_rec_link}

 return render(request, 'recipes/index.html', {
     'recs': [pop_rec, rate_rec]
 })

def browse(request):
 recipe_list = Recipe.objects.order_by("-review_count")
 paginator = Paginator(recipe_list, 12)

 page_number = request.GET.get('page')
 page_obj = paginator.get_page(page_number)
 
 return render(request, 'recipes/browse.html', {
     'page_obj': page_obj
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
	#return render(request, 'recipes/detail.html', {'recipe': recipe, 'steps': steps, 'ingredients': ingredients, 'url': url})
		
  