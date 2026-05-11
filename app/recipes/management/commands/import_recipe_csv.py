from django.core.management.base import BaseCommand
from django.conf import settings
import pandas as pd
from pathlib import Path
from django.contrib.auth.hashers import make_password
import re

from recipes.models import Recipe
from django.contrib.auth.models import User


APP_DIR = Path(settings.BASE_DIR).resolve().parent

class Command(BaseCommand):
	help = 'Import data from a CSV file'

	#def add_arguments(self, parser):
	#		parser.add_argument('csv_file', type=str)

	def handle(self, *args, **options):
		file_path = APP_DIR / 'data/recipes.csv'
		df = pd.read_csv(file_path)

		df_sample = df.drop_duplicates(subset = ['AuthorId']).sample(n = 100, random_state = 641).fillna(0)

		user_instances = [
			User(
				pk = row['AuthorId'],
				username = row['AuthorName'],
				email = row['AuthorName'].lower().replace(' ', '_') + '@food.com',
				password = make_password('1234')
			)
			for _, row in df_sample.iterrows()
		]

		User.objects.bulk_create(user_instances)
		self.stdout.write(self.style.SUCCESS('Successfully imported user data'))

		recipe_instances = [
			Recipe(
				id = row['RecipeId'],
				name = row['Name'],
				contributor = User.objects.get(pk = row['AuthorId']),
				prep_time = row['PrepTime'],
				cook_time = row['CookTime'],
				minutes = row['TotalTime'],
				date_published = pd.to_datetime(row['DatePublished'], format = 'mixed'),
				description = row['Description'],
				images = re.sub(r'(c\()|\)|"', '', row['Images']).split(', ')[0],
				category = row['RecipeCategory'],
				keywords = row['Keywords'],
				ingredient_quantities = row['RecipeIngredientQuantities'],
				ingredients = row['RecipeIngredientParts'],
				aggregated_rating = row['AggregatedRating'],
				review_count = row['ReviewCount'],
				calories = row['Calories'],
				fat_content = row['FatContent'],
				saturated_fat_content = row['SaturatedFatContent'],
				cholesterol_content = row['CholesterolContent'],
				sodium_content = row['SodiumContent'],
				carbohydrates_content = row['CarbohydrateContent'],
				fiber_content = row['FiberContent'],
				sugar_content = row['SugarContent'],
				protein_content = row['ProteinContent'],
				servings = row['RecipeServings'],
				recipe_yield = row['RecipeYield'],
				instructions = row['RecipeInstructions']
			) for _, row in df_sample.iterrows()
		]

		Recipe.objects.bulk_create(recipe_instances)
		self.stdout.write(self.style.SUCCESS('Successfully imported recipe data'))
		