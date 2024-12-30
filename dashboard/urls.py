from django.urls import path

from dashboard.views import get_weather
from dashboard.views import call_report
from dashboard.views import user_get_history_report
from dashboard.views import worker_get_report_list
from dashboard.views import log_out
from dashboard.views import save_user_info
from dashboard.views import get_phone_number
from dashboard.views import renew_password
from dashboard.views import get_user_info
from dashboard.views import assign_order
from dashboard.views import complete_report
from dashboard.views import cancel_report
from dashboard.views import reset_email_send_code
from dashboard.views import reset_email

from dashboard.views import get_staff_of_same_day


urlpatterns = [
    path('getWeatherApiKey/', get_weather),
    path('call_report/', call_report),
    path('user_get_history_report/', user_get_history_report),
    path('worker_get_report_list/', worker_get_report_list),
    path('logout/', log_out),

    path('savePhoneNumber/', save_user_info),
    path('getPhoneNumber/', get_phone_number),
    path('renew_password/', renew_password),
    path('get_user_info/', get_user_info),
    path('assign_order/', assign_order),
    path('complete_report/', complete_report),
    path('cancel_report/', cancel_report),
    path('reset_email_send_code/', reset_email_send_code),
    path('reset_email/', reset_email),

    path('today_workers/', get_staff_of_same_day),

]