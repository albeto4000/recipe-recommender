from django.apps import AppConfig
from django.conf import settings
import os

import gdown
import joblib

import pandas as pd

class RecipesConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'recipes'

	rec_models = {
		'popular': None,
		'slim': None,
		'explicit_mf': None,
		'implicit_mf': None
	}

	tfidf_matrix = None
	df = None
	recipe_indices = None
	
	def ready(self):
		from . import similar_items as similar_items
		from .models import Recipe

		if not os.path.isdir('models'):
			gdown.download_folder('https://drive.google.com/drive/folders/17UOKeGdRGuplmA7c6B90kRQPBe_kUUWt?usp=sharing', quiet=False)

		for model in self.rec_models.keys():
			self.rec_models[model] = joblib.load(os.path.join(settings.BASE_DIR, 'models/' + model + '_pipeline.pkl'))

		self.df = pd.DataFrame.from_records(Recipe.objects.all().values('id', 'category', 'keywords'))
		_, self.tfidf_matrix = similar_items.fit_tfidf(self.df)
		self.recipe_indices = pd.Series(self.df.index, index=self.df['id']).drop_duplicates()