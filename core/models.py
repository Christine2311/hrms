from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL


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

    def __str__(self):
        return self.username


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=10, blank=True, null=True)
    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'employee'},
        related_name='managed_departments'
    )
    location = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )

    position = models.CharField(max_length=200)

    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return f"Employee #{self.id}"  # fallback for safety
    


    
    
class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {'Read' if self.read else 'Unread'}"
    
    

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    class Meta:
     unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.status}"
    
   
TICKET_TYPES = (
    ('leave', 'Leave Request'),
    ('complaint', 'Official Complaint'),
    ('clearance', 'Clearance Request'),
)

TICKET_STATUS = (
    ('pending', 'Pending Review'),
    ('approved', 'Approved/Resolved'),
    ('rejected', 'Rejected/Closed'),
)

# 2. Now define your Model
class Ticket(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tickets')
    
    # Refer to the variables defined above
    category = models.CharField(max_length=20, choices=TICKET_TYPES, default='leave')
    status = models.CharField(max_length=20, choices=TICKET_STATUS, default='pending')
    
    subject = models.CharField(max_length=200)
    description = models.TextField()
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    admin_comment = models.TextField(null=True, blank=True, help_text="Reason for rejection or approval notes")

    def __str__(self):
        # This helper method uses the 'Human Readable' name from the choices
        return f"{self.get_category_display()} - {self.employee.user.username}"
    




class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Links the task to a specific Department
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='tasks')
    
    # Links the task to the Employee doing the work
    assigned_to = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='assigned_tasks')
    
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.assigned_to.user.username}"