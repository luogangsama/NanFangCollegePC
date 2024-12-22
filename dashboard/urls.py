from django.urls import path

from dashboard.views import modifyPassword
from dashboard.views import get_weather
from dashboard.views import call_report
from dashboard.views import user_get_history_report

urlpatterns = [
    path('modifyPassword/', modifyPassword),
    path('getWeatherApiKey/', get_weather),
    path('call_report/', call_report),
    path('user_get_history_report/', user_get_history_report)
]