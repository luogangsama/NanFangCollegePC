from django.contrib import admin

# Register your models here.
from .models import Users
from .models import call_report_table
from .models import UserProfile
admin.site.register(Users)
admin.site.register(call_report_table)
admin.site.register(UserProfile)
