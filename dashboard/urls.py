from django.urls import path

from dashboard.views import modifyPassword
from dashboard.views import get_weather
from dashboard.views import call_report

urlpatterns = [
    path('modifyPassword/', modifyPassword),
    path('getWeatherApiKey/', get_weather),
    path('call_report/', call_report),
]