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
		file_path = APP_DIR / 'data/recipes.csv'
		df = pd.read_csv(file_path)

		df_sample = df.drop_duplicates(subset = ['AuthorId']).sample(n = 100, random_state = 641).fillna(0)
		
		file_path = APP_DIR / 'data/reviews.csv'
		df = pd.read_csv(file_path)

		ratings = df[df['RecipeId'].isin(df_sample['RecipeId'])]

		user_instances = [
			User(
				pk = row['AuthorId'],
				username = row['AuthorName'],
				email = row['AuthorName'].lower().replace(' ', '_') + '@food.com',
				password = make_password('1234')
			)
			for _, row in ratings.drop_duplicates(subset = ['AuthorId']).iterrows()
		]

		User.objects.bulk_create(user_instances, ignore_conflicts = True)
		self.stdout.write(self.style.SUCCESS('Successfully imported user data'))

		rating_instances = [
			Rating(
				pk = row['ReviewId'],
				user = User.objects.get(pk = row['AuthorId']),
				recipe = Recipe.objects.get(pk = row['RecipeId']),
				rating = row['Rating'],
				review = row['Review'],
				date_submitted = pd.to_datetime(row['DateSubmitted'], format = 'mixed')
			) for _, row in ratings.iterrows()
		]

		Rating.objects.bulk_create(rating_instances)
		self.stdout.write(self.style.SUCCESS('Successfully imported rating data'))