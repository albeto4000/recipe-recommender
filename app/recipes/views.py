from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localdate
from django.db.models import Avg
from django.conf import settings
from django.contrib import messages

from django.apps import apps

import re
import json
import ast
import numpy as np

import lenskit
from lenskit import recommend

from functools import reduce
from operator import or_

from .models import Recipe, Rating


#This is the index, or the home page
def index(request):
	#I'll set up multiple rating sections on the home page. Each of these will send the user to the browse view (recipes:browse),
	#with parameters to filter the results
	base_url = reverse("recipes:browse")

	rec_list = []

	#The first section recommends popular recipes, or recipes with the most ratings
	#Reads the pop_scorer pipe from the models directory
	ml_config = apps.get_app_config('recipes')
	pop_pipe = ml_config.pop

	#Gets the IDs of the 8 recipes with the most ratings
	pop_rec_category = "popular recipes"
	#Gets the item IDs of the top 8 models recommended by the pop_scorer
	#Pop_scorer does not need user_id to make recommendations
	pop_rec_nums = recommend(pop_pipe, None, n=8).to_df()['item_id'].values
	#Fetches the recipes corresponding to those 8 IDs
	pop_rec_list = Recipe.objects.filter(id__in=pop_rec_nums)
	#Browse shows all recipes by popularity as its default, so I won't encode any arguments in the url
	pop_rec_link = base_url
	#Creates a dictionary to represent the pop_recs section
	#The index view takes a list of dictionaries like this and formats them into HTML using the recipe-display.html template
	rec_list.append({
		'category': pop_rec_category,
		'list': pop_rec_list,
		'url': pop_rec_link
	})

	if request.user.is_authenticated:
		#Lists model names, which will be displayed above the recommendation sections
		model_names = ['item_item', 'user_user', 'slim', 'explicit_mf', 'implicit_mf'] #'item_item_implicit', 'explicit_mf', 'implicit_mf', 'slim'
		#Gets the recommender models, which are loaded on app startup
		models = [ml_config.item_item, ml_config.user_user, ml_config.slim, ml_config.explicit_mf, ml_config.implicit_mf]
		
		#Fetches the recipes the user has rated, and the ratings they assigned
		user_recipes = request.user.rating_set.values_list('recipe', flat = True)
		user_ratings = request.user.rating_set.values_list('rating', flat = True)

		#Adds a recommendation section for recipes the user has recently rated 4 stars or higher
		make_again = request.user.rating_set.filter(rating__gte=4).order_by("-rating", "-date_submitted").values_list('recipe')[:8]
		rec_list.append({
			'category': 'make again',
			'list': Recipe.objects.filter(id__in=make_again),
			'url': reverse('recipes:reviews')
		})

		#Creates an itemlist, history_items, that stores a user's item interactions
		history_items = lenskit.data.ItemList(user_recipes, rating=user_ratings)
		#Initializes a lenskit RecQuery using the user's item interactions
		#We use RecQuery over user_id to ensure recommenders can integrate new users and new interactions
		query = lenskit.data.RecQuery(user_id = -1, history_items = history_items)

		for model_name, model in zip(model_names, models):
			#Gets 8 recommendations from the current model and extracts item IDs
			recs = recommend(model, query, n = 8).to_df()['item_id'].values
			#Fetches the 8 recipes that correspond to the recommended IDs
			pipe_rec_list = Recipe.objects.filter(id__in=recs)
			#Creates a new recommendation section using the model name and recommended recipes
			rec_list.append({
				'category': model_name,
				'list': pipe_rec_list,
				'url': base_url
			})

	#Render displays a template with parameters included as a dict
	#The index view takes parameter 'recs', a list of dictionaries that represent the recommendation sections
	return render(request, 'recipes/index.html', {
		'recs': rec_list
	})	


#The browse view allows users to click through a filtered set of recipes
def browse(request):
	#This object will be used to filter the recipes fetched from the database and displayed
	query = Q()
	
	#Requests can be two types: GET and POST
	#GET requests send data through the URL and is intended to fetch data from the database
	#POST requests send data through the request body and is used for creating/updating the database
	#Here, we'll retrieve the filters sent through the GET request
	name = request.GET.get('name')
	if name:
		#If one of the filters is name, filter for all recipes whose name contains that value, ignoring capitalization
		query &= Q(name__icontains=name)

	category = request.GET.get('category')
	if category:
		query &= Q(category=category)

	keywords = request.GET.get('keywords')
	if keywords:
		query &= Q(keywords__icontains=keywords)

	#Queries the database using the filters defined above
	recipe_list = Recipe.objects.filter(query).order_by('-review_count')

	#There are over 500,000 recipes in the database, and a page displaying all of them would take forever to load
	#Django offers a class called the Paginator, which takes a queryset and splits it into subsets called pages
	#I'll display the recipes 12 at a time, to ensure the display looks good on every page size using Bootstrap
	#On large pages, this will be displayed as 3 rows of 4 recipes. Medium will change this to 4 rows of 3, and small will display 12 rows of 1
	#12 is easy to divide. If we wanted, we could display 6 rows of 2, then 12 rows of 1 only on extra small (xs) screen widths
	paginator = Paginator(recipe_list, 12)

	#I'll send the current page as a GET parameter. When the user clicks the next page, this value will increment and the next page's content will be returned
	page_number = request.GET.get('page')
	#Gets the 12 recipes associated with the current page number
	page_obj = paginator.get_page(page_number)

	return render(request, 'recipes/browse.html', {
		'page_obj': page_obj
	})


#This view displays the details of a recipe, including its ingredients, instructions, and related recipes
def detail(request, recipe_id):
	#get_object_or_404 checks to see if the recipe exists. Otherwise, this page will display a 404 (object not found) error
	recipe = get_object_or_404(Recipe, pk = recipe_id)

	#Some of the web-scraped ingredient text links to pages that no longer exist, and therefore displays as '[ error ]'
	#For these pages, we'll instead use the unitless ingredient text from the original dataset. Otherwise, we'll parse that
	#data from string versions of lists into actual lists using ast.literal_eval
	#
	#Any use of an eval() function is dangerous, as it leaves the site vulnerable to SQL injection attacks
	#Users can write Python or SQL code as a new recipe, and the website will automatically run it
	#Because this is an academic project, and not an actual website, we'll trust the users to interact with it responsibly
	if recipe.ingredient_text != "['error']":
		ingredients = ast.literal_eval(recipe.ingredient_text)
	else:
		ingredients = re.split(r'",\s*"', recipe.ingredients[3:-2])
	#Converts the ingredient amounts and recipe instructions into lists using regex
	ing_amounts = recipe.ingredient_quantities[2:-1].replace('\"', '').split(', ')
	steps = re.split(r'",\s*"', recipe.instructions[3:-2])
    
	#Removes the \D prefix from the recipe minutes
	minutes = re.sub(r'\D', '', recipe.minutes)

	#The nutrition information will be displayed as a table in a modal. I'll use a for-loop to create the table rows, meaning the 
	#nutrition information needs to be formatted as a list. Each row will display the label, nutrition value (with units), and the percent of daily value
	nutrition_labels = ['Calories', 'Total Fat', 'Saturated Fat', 'Cholesterol', 'Sodium', 'Total Carbohydrate', 'Dietary Fiber', 'Sugars', 'Protein']
	nutrition_vals = [recipe.calories, recipe.fat_content, recipe.saturated_fat_content, recipe.cholesterol_content, recipe.sodium_content, recipe.carbohydrates_content, recipe.fiber_content, recipe.sugar_content, recipe.protein_content]
	#Nutrient daily values sourced from the FDA (https://www.fda.gov/food/nutrition-facts-label/daily-value-nutrition-and-supplement-facts-labels)
	nutrition_dv = [2000, 78, 20, 300, 2300, 275, 28, 50, 50]
	nutrition_units = ['', 'g', 'g', 'mg', 'mg', 'g', 'g', 'g', 'g']
	nutrition_pct = [round((val / dv) * 100, 2) for val, dv in zip(nutrition_vals, nutrition_dv)]

	keywords = re.split(r'",\s*"', recipe.keywords[3:-2])

	#Users can submit ratings on this page. If a user has already rated this recipe, their rating should automatically display in the rating input
	#If the user is currently signed in (is_autheticated), I'll determine if they've rated this recipe, then fetch their rating and review
	if request.user.is_authenticated:
		try:
			user_rating = Rating.objects.get(user=request.user, recipe=recipe)
			score = user_rating.rating
			review = user_rating.review
		except Rating.DoesNotExist:
			score = None  # User hasn't rated this recipe yet
			review = ""
	else:
		score = None
		review = ""

	#Loads the model from the Django app config
	ml_config = apps.get_app_config('recipes')
	#Fetches the ItemKNN scorer similarity matrix
	knn_sim = ml_config.item_item.component('scorer').sim_matrix.to_scipy()
	if recipe_id < knn_sim.shape[0]:
		#Gets the similarity of every recipe to the current one, sorts from least to greatest, then retrieves the IDs of the 4 most similar
		knn_closest = np.argsort(knn_sim[recipe_id, :].toarray().ravel())[-4:]
		
		#Fetches the recipes by ID
		similar_recipes = Recipe.objects.filter(id__in=knn_closest)
	else:
		similar_recipes = None

	#Renders the page (with a lot of parameters)
	return render(request, 'recipes/detail.html', {
		'recipe': recipe, 
		'ingredients': list(zip(ing_amounts, ingredients)), 
		'n_ingredients': len(ingredients),
		'steps': steps, 
		'minutes': minutes,
		'nutrition_info': list(zip(nutrition_labels, nutrition_vals, nutrition_units, nutrition_pct)),
		'rating': score,
		'review': review,
		'keywords': keywords,
		'similar_recipes': similar_recipes
  })


#The search view will work similarly to the browse view, but with a sidebar for the user to add filters
#To make sure the user does not need to reload their page for their filters to apply, I'll use Ajax to get the filtered recipes, then
#use jQuery to update the section of the page that displays those recipes. 
#See the query route and the Javascript on search.html for that implementation
def search(request):
	#By default, this page will display all recipes, ordered by # of ratings descending
	recipe_list = Recipe.objects.all().order_by('-review_count')

	#Creates a paginator to display only 12 recipes at a time
	paginator = Paginator(recipe_list, 12)

	#Displays the current paginator page
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	
	#Filters will be displayed as dropdowns with checkboxes
	#To define the filter categories, the labels that appear, the values those labels correspond to, and the database column that
	#the filter applies to, I'll define a list of dictionaries
	season_filter = {
		'category': 'season', 
		'choices': [
			('spring', 'spring'), 
			('summer', 'summer'), 
			('fall', 'fall'), 
			('winter', 'winter')], 
		'filters': 'keywords'
	}

	#Some filters, like seafood, apply one label to multiple keywords
	#This process slows down the page rendering (as the database has to do string matching for each keyword across all
	#500,000 recipes), so we'll look into adding new keywords on database creation
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
			('seafood', '|'.join(seafood)) #filters with multiple keywords combine those into one string, separated by |
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

	#Displays the search page with the filters defined above and the paginated recipe list
	return render(request, 'recipes/search.html', {
		'filters': [season_filter, protein_filter, diet_filter, cook_time_filter],
		'page_obj': page_obj
	})


#The search page displays the search results without needing to reload the page
#To accomplish this, the query route defined below 
def query(request):
	#This object will be used to filter the recipes fetched from the database and displayed
	query = Q()

	#The AJAX call sends its request as JSON
	#json.loads unpacks that data into a Python dict
	res = json.loads(request.body)

	#Users can select multiple filters, each of which may apply to one of many columns
	for filter_col, filter_val in zip(res['filter_col'], res['filter_val']):
		#If the user filters by keywords, split the result by | (to handle multiple keywords), then filter for rows whose keywords
		#column contains any of the selected
		if filter_col == 'keywords':
			values = filter_val.split('|')
			keyword_query = reduce(
				or_,
				(Q(keywords__icontains = v) for v in values)
			)
			#Adds the keywords filter to the query
			query &= keyword_query
		#Filters by category, ignoring capitalization
		elif filter_col == 'category':
			query &= Q(category__in=filter_val)
		#Filters by name, ignoring capitalization
		elif filter_col == 'name':
			query &= Q(name__icontains=filter_val)

	#Returns any rows matching all of the filters, ordered by popularity
	recipe_list = Recipe.objects.filter(query).order_by('-review_count')

	#Chunks the resulting recipes into pages of 12
	paginator = Paginator(recipe_list, 12)

	#Fetches the 12 recipes corresponding to the current page
	page_number = res['page']
	page_obj = paginator.get_page(page_number)

	#Returns only the recipe display content, not the entire webpage content
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return render(request, 'recipes/paginated-recipes.html', {
			'page_obj': page_obj,
			'filters_selected': res['filter_label']
	})


#This route allows users to log in with their email
#require_POST means a user cannot attempt to log in any other way than the login form
@require_POST
def login_view(request):
	#Gets the email and password sent to the back-end (by post)
	email = request.POST['email']
	password = request.POST['password']

	#Gets the username associated with the entered email
	username = get_user_model().objects.get(email = email).username
	#Attempts to authenticate the user given the entered username and password
	user = authenticate(request, username = username, password = password)

	#If the user credentials are valid, log in and redirect to the current webpage
	if user is not None:
		login(request, user)

		next_url = request.POST.get("next")

		if next_url:
			return redirect(next_url)
		
		return redirect("recipes:index")
	#If the user is not valid, send an error message, then redirect to the current webpage
	else:
		messages.error(request, "Invalid email or password.")

		next_url = request.POST.get("next")

		if next_url:
			return redirect(next_url)
		return redirect("recipes:index")


#Logs the user out
def logout_view(request):
    logout(request)

    return redirect("recipes:index")

@require_POST
def signup_view(request):
	#Gets the email and password sent to the back-end (by post)
	email = request.POST['email']
	password = request.POST['password']
	
	if not get_user_model().objects.filter(email=email).exists():
		# 2. Safely create the user with a hashed password
		user = get_user_model().objects.create_user(
				username=email.split('@')[0],
				email=email,
				password=password
		)

		print("User created with email", email)
		login(request, user)
		return redirect("recipes:index")
	else:
		messages.error(request, "A user with email " + email + " already exists")
		print("User already exists")
		return redirect("recipes:index")


#Route for users to submit new recipe ratings/reviews
#login_required means that a user who is not signed in cannot rate recipes
@login_required
def submit_rating(request):
	#Gets the ID of the current recipe
	recipe_id = int(request.POST.get('recipe_id'))
	#Attempts to find the recipe iwth the given ID. Returns 404 error otherwise
	recipe = get_object_or_404(Recipe, pk=recipe_id)

	#rating>0 means the user has clicked a star to rate, not clicked the star of their current rating to remove it
	if int(request.POST.get('rating')) != 0:
		#Attempts to create a new rating, or updates the rating if it already exists
		#To ensure that duplicate ratings are not created, I list rating, review, and date_submitted under defaults
		#This means that if any of these values change, Django will not consider the new entry as a new rating, but instead updates
		#the existing one corresponding to the entered user ID and recipe ID
		new_rating, created = Rating.objects.update_or_create(
			user=request.user,
			recipe=recipe,
			defaults={
				'rating': request.POST.get('rating'),
				'review': request.POST.get('review'),
				'date_submitted': localdate()
			}
		)	
	#If rating == 0, that means the user is attempting to remove their rating
	else:
		#Finds the rating corresponding to the user and recipe IDs, then deletes that rating
		Rating.objects.get(user=request.user, recipe=recipe).delete()

	#Updates the rating_count and aggregated_rating of the associated recipe
	rating_count = Rating.objects.filter(recipe=recipe).count()
	Recipe.objects.filter(id=recipe_id).update(review_count=rating_count)
	if rating_count > 0:
		avg_rating = round(Rating.objects.filter(recipe=recipe).aggregate(Avg('rating'))['rating__avg'] * 2) / 2
		Recipe.objects.filter(id=recipe_id).update(aggregated_rating=avg_rating)
	else:
		Recipe.objects.filter(id=recipe_id).update(aggregated_rating=0)

	#Redirects to the detail page for the current recipe
	return detail(request, recipe_id)


@login_required
def reviews(request):
	return render(request, 'recipes/user_reviews.html')