from django.urls import path, include
from . import views

app_name = "recipes"
urlpatterns = [
		path("", views.index, name = "index"),
		path("<int:recipe_id>/", views.detail, name = "detail"),
		path("browse/", views.browse, name = "browse"),
		path("search/", views.search, name = "search"),
		path("query/", views.query, name = "query"),
    path('login/', views.login_view, name = "login"),
		path('logout/', views.logout_view, name = "logout"),
		path('signup/', views.signup_view, name = "signup"),
		path('rate/', views.submit_rating, name = "rate"),
		path('reviews/', views.reviews, name = "reviews")
]