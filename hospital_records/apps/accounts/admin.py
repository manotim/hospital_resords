from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'user_type', 'department', 'phone_number']
    list_filter = ['user_type', 'department']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']