from django.core.management.base import BaseCommand
import pandas as pd

from recipes.models import Recipe
from django.contrib.auth.models import User

class Command(BaseCommand):
		help = 'Import data from a CSV file'

		#def add_arguments(self, parser):
		#		parser.add_argument('csv_file', type=str)

		def handle(self, *args, **options):
				#df = pd.read_csv(options['csv_file'])
				df = pd.read_csv('C:/Users/albet/Documents/Drexel/projects/recipe-recommender/data/recipes.csv')

				df_sample = df.drop_duplicates(subset = ['AuthorId']).sample(n = 100, random_state = 641).fillna(0)

				instances = [
					Recipe(
						id = row['RecipeId'],
						name = row['Name'],
						contributor = User.objects.get(pk = row['AuthorId']),
						prep_time = row['PrepTime'],
						cook_time = row['CookTime'],
						minutes = row['TotalTime'],
						date_published = pd.to_datetime(row['DatePublished'], format = 'mixed'),
						description = row['Description'],
						images = row['Images'],
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

				Recipe.objects.bulk_create(instances)
				self.stdout.write(self.style.SUCCESS('Successfully imported data'))