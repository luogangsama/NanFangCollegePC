from django.urls import path
from message_board.views import get_message_record

urlpatterns = [
    path('get_message_record/', get_message_record)
]