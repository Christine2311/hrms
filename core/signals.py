# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Employee, Notification, CustomUser

@receiver(post_save, sender=Employee)
def notify_admin_new_employee(sender, instance, created, **kwargs):
    if created:
        admins = CustomUser.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"New employee '{instance.user.username}' has been added"
            )