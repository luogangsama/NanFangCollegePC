from django.urls import path
from unit.views import user_get_city_and_weather

urlpatterns = [
    path('user_get_ip/', user_get_city_and_weather),
]