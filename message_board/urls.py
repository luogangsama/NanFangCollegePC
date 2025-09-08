from django.urls import path
from message_board.views import get_message_record
from message_board.views import get_message_list

urlpatterns = [
    path('get_message_record/', get_message_record),
    path('get_message_list/'. get_message_list)
]