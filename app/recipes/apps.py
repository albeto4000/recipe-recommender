from django.apps import AppConfig
from django.conf import settings
import os
import joblib

class RecipesConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'recipes'

	rec_models = {
		'popular': None,
		'slim': None,
		'explicit_mf': None,
		'implicit_mf': None
	}
	
	def ready(self):
		for model in self.rec_models.keys():
			self.rec_models[model] = joblib.load(os.path.join(settings.BASE_DIR, '../models/' + model + '_pipeline.pkl'))

		