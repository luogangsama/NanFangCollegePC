from django.contrib import admin

# Register your models here.
from .models import call_report_table
from .models import UserProfile
from .models import report_message_board_record
admin.site.register(call_report_table)
admin.site.register(UserProfile)
admin.site.register(report_message_board_record)