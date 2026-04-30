from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Recipe, Rating

import json

class IndexView(generic.ListView):
    template_name = "recipes/index.html"
    context_object_name = "latest_recipe_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Recipe.objects.order_by("-id")[:5]


class DetailView(generic.DetailView):
    model = Recipe
    template_name = "recipes/detail.html"
     

    