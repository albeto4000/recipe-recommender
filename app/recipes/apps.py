from django.apps import AppConfig
from django.conf import settings
import os
import joblib

models = ['item_item', 'user_user', 'slim', 'explicit_mf', 'implicit_mf']

class RecipesConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'recipes'

	pop = None
	item_item = None
	user_user = None
	slim = None
	explicit_mf = None
	implicit_mf = None
	
	def ready(self):
		self.pop = joblib.load(os.path.join(settings.BASE_DIR, '../models/popular_pipeline.pkl'))
		self.item_item = joblib.load(os.path.join(settings.BASE_DIR, '../models/item_item_pipeline.pkl'))
		self.user_user = joblib.load(os.path.join(settings.BASE_DIR, '../models/user_user_pipeline.pkl'))
		self.slim = joblib.load(os.path.join(settings.BASE_DIR, '../models/slim_pipeline.pkl'))
		self.explicit_mf = joblib.load(os.path.join(settings.BASE_DIR, '../models/explicit_mf_pipeline.pkl'))
		self.implicit_mf = joblib.load(os.path.join(settings.BASE_DIR, '../models/implicit_mf_pipeline.pkl'))

		