from django.core.management.base import BaseCommand
from django.conf import settings
import pandas as pd
from pathlib import Path
from django.contrib.auth.hashers import make_password
import re

from recipes.models import Recipe, Rating
from django.contrib.auth.models import User

from datetime import datetime


APP_DIR = Path(settings.BASE_DIR).resolve().parent

class Command(BaseCommand):
	help = 'Import data from a CSV file'

	#def add_arguments(self, parser):
	#		parser.add_argument('csv_file', type=str)

	def handle(self, *args, **options):
		recipe_file_path = APP_DIR / 'data/recipes.csv'
		ratings_file_path = APP_DIR / 'data/reviews.csv'

		#Import recipe data
		recipe_df = pd.read_csv(recipe_file_path)
		ratings_df = pd.read_csv(ratings_file_path)

		#Converts recipe data_published data to datetime
		recipe_df['DatePublished'] = pd.to_datetime(
				recipe_df['DatePublished'],
				errors='coerce'
		)

		#Selects the first image link for each recipe (if exists)
		recipe_df['Images'] = (
				recipe_df['Images']
				.str.replace(r'(c\()|\)|"', '', regex=True)
				.str.split(', ')
				.str[0]
		)

		#Handles any missing integer values
		recipe_df.fillna(0, inplace = True);

		ratings_df['DateSubmitted'] = pd.to_datetime(
				ratings_df['DateSubmitted'],
				errors='coerce'
		)

		recipe_sample = recipe_df.drop_duplicates(subset = ['AuthorId']).sample(n = 100, random_state = 641).fillna(0)
		ratings_sample = ratings_df[ratings_df['RecipeId'].isin(recipe_sample['RecipeId'])]
		
		#Selects all user table columns and drops duplicates
		recipe_users = (
				pd.concat([recipe_sample[['AuthorId', 'AuthorName']], ratings_sample[['AuthorId', 'AuthorName']]])
				.drop_duplicates(subset=['AuthorId'])
		)

		recipe_users['Email'] = recipe_users['AuthorName'].str.lower().str.replace(' ', '_') + '@food.com'
		recipe_users['Pass'] = make_password('1234')

		self.stdout.write(self.style.NOTICE(datetime.now().strftime('%H:%M:%S') + " Beginning user import"))

		#Populates user table using all recipe and review authors
		user_instances = [
				User(
						pk = row.AuthorId,
						username = row.AuthorName,
						email = row.Email,
						password = row.Pass,
				)
				for row in recipe_users.itertuples(index=False)
		]

		User.objects.bulk_create(
				user_instances,
				ignore_conflicts=True,
				batch_size=5000,
		)

		self.stdout.write(datetime.now().strftime('%H:%M:%S') + self.style.SUCCESS('Successfully imported user data'))

		#Selects all recipe_author user objects
		users = User.objects.in_bulk(field_name='id')

		self.stdout.write(self.style.NOTICE(datetime.now().strftime('%H:%M:%S') + " Beginning recipe import"))

		#Populates recipe table using CSV data
		recipe_instances = [
				Recipe(
						id=row.RecipeId,
						name=row.Name,
						contributor=users.get(row.AuthorId),
						prep_time=row.PrepTime,
						cook_time=row.CookTime,
						minutes=row.TotalTime,
						date_published=row.DatePublished,
						description=row.Description,
						images=row.Images,
						category=row.RecipeCategory,
						keywords=row.Keywords,
						ingredient_quantities=row.RecipeIngredientQuantities,
						ingredients=row.RecipeIngredientParts,
						aggregated_rating=row.AggregatedRating,
						review_count=row.ReviewCount,
						calories=row.Calories,
						fat_content=row.FatContent,
						saturated_fat_content=row.SaturatedFatContent,
						cholesterol_content=row.CholesterolContent,
						sodium_content=row.SodiumContent,
						carbohydrates_content=row.CarbohydrateContent,
						fiber_content=row.FiberContent,
						sugar_content=row.SugarContent,
						protein_content=row.ProteinContent,
						servings=row.RecipeServings,
						recipe_yield=row.RecipeYield,
						instructions=row.RecipeInstructions,
				)
				for row in recipe_sample.itertuples(index=False)
		]

		Recipe.objects.bulk_create(
				recipe_instances,
				ignore_conflicts=True,
				batch_size=5000,
		)

		self.stdout.write(datetime.now().strftime('%H:%M:%S') + self.style.SUCCESS('Successfully imported recipe data'))

		#Selects all recipes
		recipes = Recipe.objects.in_bulk(field_name='id')

		self.stdout.write(self.style.NOTICE(datetime.now().strftime('%H:%M:%S') + " Beginning ratings import"))

		rating_instances = [
				Rating(
						pk=row.ReviewId,
						user=users.get(row.AuthorId),
						recipe=recipes.get(row.RecipeId),
						rating=row.Rating,
						review=row.Review,
						date_submitted=row.DateSubmitted,
				)
				for row in ratings_sample.itertuples(index=False)
		]

		Rating.objects.bulk_create(
				rating_instances,
				ignore_conflicts=True,
				batch_size=5000,
		)

		self.stdout.write(datetime.now().strftime('%H:%M:%S') + self.style.SUCCESS('Successfully imported ratings data'))