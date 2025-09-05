from django.urls import path
# from unit.views import user_get_city_and_weather
from unit.views import userWeather

urlpatterns = [
    # path('user_get_city_and_weather/', user_get_city_and_weather),
    path('user_get_city_and_weather/', userWeather),
]
