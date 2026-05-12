from django.core.management.base import BaseCommand
from django.conf import settings
import pandas as pd
from pathlib import Path
from django.contrib.auth.hashers import make_password
import re

from recipes.models import Recipe, Rating
from django.contrib.auth.models import User


APP_DIR = Path(settings.BASE_DIR).resolve().parent

class Command(BaseCommand):
	help = 'Import data from a CSV file'

	#def add_arguments(self, parser):
	#		parser.add_argument('csv_file', type=str)

	def handle(self, *args, **options):
		recipe_file_path = APP_DIR / 'data/recipes.csv'
		recipe_df = pd.read_csv(recipe_file_path)

		recipe_sample = recipe_df.drop_duplicates(subset = ['AuthorId']).sample(n = 100, random_state = 641).fillna(0)
		
		ratings_file_path = APP_DIR / 'data/reviews.csv'
		ratings_df = pd.read_csv(ratings_file_path)

		ratings_sample = ratings_df[ratings_df['RecipeId'].isin(recipe_sample['RecipeId'])]

		user_instances = [
			User(
				pk = row['AuthorId'],
				username = row['AuthorName'],
				email = row['AuthorName'].lower().replace(' ', '_') + '@food.com',
				password = make_password('1234')
			)
			for _, row in ratings_sample.drop_duplicates(subset = ['AuthorId']).iterrows()
		]

		User.objects.bulk_create(user_instances, ignore_conflicts = True)
		self.stdout.write(self.style.SUCCESS('Successfully imported ratings user data'))

		rating_instances = [
			Rating(
				pk = row['ReviewId'],
				user = User.objects.get(pk = row['AuthorId']),
				recipe = Recipe.objects.get(pk = row['RecipeId']),
				rating = row['Rating'],
				review = row['Review'],
				date_submitted = pd.to_datetime(row['DateSubmitted'], format = 'mixed')
			) for _, row in ratings_sample.iterrows()
		]

		Rating.objects.bulk_create(rating_instances)
		self.stdout.write(self.style.SUCCESS('Successfully imported rating data'))