from django.urls import path
from unit.views import user_get_ip_and_weather
from unit.views import user_save_ip

urlpatterns = [
    path('user_get_ip/', user_get_ip_and_weather),
    path('user_save_ip/', user_save_ip),
]