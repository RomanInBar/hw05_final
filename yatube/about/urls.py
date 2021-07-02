from django.urls import path

from . import views
from .apps import AboutConfig

app_name = AboutConfig.name

urlpatterns = [
    path('author/', views.AboutAuthorView.as_view(), name='author'),
    path('tech/', views.AboutTechView.as_view(), name='tech'),
]
