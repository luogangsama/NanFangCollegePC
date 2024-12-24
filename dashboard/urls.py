from django.urls import path

from dashboard.views import modifyPassword
from dashboard.views import get_weather
from dashboard.views import call_report
from dashboard.views import user_get_history_report
from dashboard.views import log_out
from dashboard.views import save_user_info
from dashboard.views import get_phone_number


urlpatterns = [
    path('modifyPassword/', modifyPassword),
    path('getWeatherApiKey/', get_weather),
    path('call_report/', call_report),
    path('user_get_history_report/', user_get_history_report),
    path('logout/', log_out),

    path('savePhoneNumber/', save_user_info),
    path('getPhoneNumber/', get_phone_number),
]