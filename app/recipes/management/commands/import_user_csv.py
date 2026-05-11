from django.core.management.base import BaseCommand
import pandas as pd
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from pathlib import Path

class Command(BaseCommand):
		help = 'Import data from a CSV file'

		def handle(self, *args, **options):
				df = pd.read_csv('C:/Users/albet/Documents/Drexel/projects/recipe-recommender/data/recipes.csv')

				df_sample = df.drop_duplicates(subset = ['AuthorId']).sample(n = 100, random_state = 641)

				instances = [
					User(
						pk = row['AuthorId'],
						username = row['AuthorName'],
						email = row['AuthorName'].lower().replace(' ', '_') + '@food.com',
						password = make_password('1234')
					)
					for _, row in df_sample.iterrows()
				]

				User.objects.bulk_create(instances)
				self.stdout.write(self.style.SUCCESS('Successfully imported data'))