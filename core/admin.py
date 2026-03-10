from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department
# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('username', 'email', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('HR Information', {
            'fields': ('role', 'department'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('HR Information', {
            'fields': ('role', 'department'),
        }),
    )

admin.site.register(Department)