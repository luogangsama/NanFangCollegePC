from django.shortcuts import render
from django.http import JsonResponse

from unit.views import session_check
import json
import os
# Create your views here.

@session_check
def get_message_record(requests):
    data = json.loads(requests.body)
    reportId = data['reportId']

    message_record = f'./local/message_{reportId}.json'