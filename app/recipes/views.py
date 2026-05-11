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

	return render(request, 'recipes/detail.html', {
          'recipe': recipe, 
          'ingredients': list(zip(ing_amounts, ingredients)), 
					'steps': steps, 
					'minutes': minutes
  })
	#return render(request, 'recipes/detail.html', {'recipe': recipe, 'steps': steps, 'ingredients': ingredients, 'url': url})
		
  