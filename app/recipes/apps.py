from django.apps import AppConfig
from django.conf import settings
import os

from scipy.sparse import csr_matrix

import joblib

import pandas as pd

class RecipesConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'recipes'

	rec_models = {
		# 'popular': None,
		# 'slim': None,
		'implicit_mf': None
	}

	tfidf_matrix = None
	df = None
	recipe_indices = None

	def get_model(self, name):
		if self.rec_models[name] is None:
			self.rec_models[name] = joblib.load(
				os.path.join(
					settings.BASE_DIR, f"models/{name}_pipeline.pkl"
				)
			)

		return self.rec_models[name]
	
	def ready(self):
		from . import similar_items as similar_items
		from .models import Recipe

		#self.df = pd.DataFrame.from_records(Recipe.objects.all().values('id', 'category', 'keywords'))
		#_, self.tfidf_matrix = similar_items.fit_tfidf(self.df)
		self.tfidf_matrix = csr_matrix(pd.read_csv('tfidf_matrix.csv').values)

		#self.recipe_indices = pd.Series(self.df.index, index=self.df['id']).drop_duplicates()
		self.recipe_indices = pd.read_csv('recipe_indices.csv', index_col = 'id', usecols = ['id', '0']).squeeze('columns')