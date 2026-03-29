# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, Employee, Notification
from .models import Task

# ------------------------------
# CUSTOM USER ADMIN
# ------------------------------
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active')

    # ✅ wrap role in a tuple
    fieldsets = UserAdmin.fieldsets + (
        ('HR Information', {
            'fields': ('role',),  # <-- comma is mandatory
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('HR Information', {
            'fields': ('role',),  # <-- comma is mandatory
        }),
    )

# ------------------------------
# OTHER MODELS
# ------------------------------
admin.site.register(Department)
admin.site.register(Employee)
admin.site.register(Notification)  



@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'assigned_to', 'status', 'due_date')
    list_filter = ('status', 'department')
    search_fields = ('title', 'description')