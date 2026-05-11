from django.db import models
from django.conf import settings
from django.utils import timezone

class Recipe(models.Model):
	id = models.IntegerField(primary_key = True)
	name = models.CharField(max_length = 200)
	contributor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
	prep_time = models.CharField(max_length = 200)
	cook_time = models.CharField(max_length = 200)
	minutes = models.CharField(max_length = 200)
	date_published = models.DateField(default = timezone.now)
	description = models.TextField()
	images = models.TextField()
	category = models.CharField(max_length = 200)
	keywords = models.TextField()
	ingredient_quantities = models.TextField()
	ingredients = models.TextField()
	aggregated_rating = models.FloatField()
	review_count = models.IntegerField(default = 0)
	calories = models.IntegerField(default = 0)
	fat_content = models.IntegerField(default = 0)
	saturated_fat_content = models.IntegerField(default = 0)
	cholesterol_content = models.IntegerField(default = 0)
	sodium_content = models.IntegerField(default = 0)
	carbohydrates_content = models.IntegerField(default = 0)
	fiber_content = models.IntegerField(default = 0)
	sugar_content = models.IntegerField(default = 0)
	protein_content = models.IntegerField(default = 0)
	servings = models.IntegerField(default = 0)
	recipe_yield = models.CharField(max_length = 200)
	instructions = models.TextField()
	
	def __str__(self):
		return self.name

class Rating(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
	recipe = models.ForeignKey(Recipe, on_delete = models.CASCADE)
	rating = models.IntegerField()
	review = models.TextField()
	date_submitted = models.DateField(default = timezone.now)

	def __str__(self):
		return self.review
	