from django.urls import path
from unit.views import user_get_ip
from unit.views import user_save_ip
from unit.views import get_weather

urlpatterns = [
    path('user_get_ip/', user_get_ip),
    path('user_save_ip/', user_save_ip),
    path('get_weather/', get_weather),
]