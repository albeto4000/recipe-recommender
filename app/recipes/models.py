from django.db import models
from django.conf import settings

class Recipe(models.Model):
	name = models.CharField(max_length = 200)
	id = models.IntegerField(primary_key = True)
	minutes = models.IntegerField()
	contributor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
	tags = models.TextField()
	nutrition = models.CharField(max_length = 200)
	n_steps = models.IntegerField()
	steps = models.TextField()
	description = models.TextField()
	ingredients = models.TextField()
	n_ingredients = models.IntegerField()

	def __str__(self):
		return self.name

class Rating(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
	recipe = models.ForeignKey(Recipe, on_delete = models.CASCADE)
	rating = models.IntegerField()
	review = models.TextField()

	def __str__(self):
		return self.review
	