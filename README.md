Instructions to run the Django app:

1. ```python manage.py migrate``` - builds the database
2. ```python manage.py import_recipe_csv``` - populates the Users and Recipes tables with a random sample pulled from the recipes.csv file (uses random state 641)
3. ```python3 manage.py runserver```
4. Go to https://localhost:8000/recipes to view all loaded recipes
