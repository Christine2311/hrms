
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'HR / Admin'),
        ('employee', 'Employee'),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='employee'
        
        )
    department= models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True
    )
    



class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name