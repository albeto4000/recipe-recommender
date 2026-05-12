from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
import re
import pandas as pd

from .models import Recipe, Rating

		
def index(request):
 recipe_list = Recipe.objects.order_by("id")
 
 return render(request, 'recipes/index.html', {
     'latest_recipe_list': recipe_list
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
		
  