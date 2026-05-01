from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Recipe, Rating

import json
import ast

class IndexView(generic.ListView):
    template_name = "recipes/index.html"
    context_object_name = "latest_recipe_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Recipe.objects.order_by("-id")[:5]


def detail(request, recipe_id):
    #model = Recipe
    #template_name = "recipes/detail.html"
    recipe = get_object_or_404(Recipe, pk = recipe_id)
    ingredients = list(ast.literal_eval(recipe.ingredients))
    steps = list(ast.literal_eval(recipe.steps))
    return render(request, 'recipes/detail.html', {'recipe': recipe, 'steps': steps, 'ingredients': ingredients})

    