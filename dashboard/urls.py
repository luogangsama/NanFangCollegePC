from django.urls import path

from dashboard.views import modifyPassword
from dashboard.views import get_weather

urlpatterns = [
    path('modifyPassword/', modifyPassword),
    path('getWeatherApiKey/', get_weather),
]