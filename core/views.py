import json
from django.shortcuts import render,get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout

from django.contrib import messages 

from .forms import DepartmentForm
from django.utils import timezone
from django.db.models import Count


import datetime


from django.contrib.auth.hashers import make_password

from .models import CustomUser, Attendance, Task, Ticket
from .models import Department, Employee, Notification
from .decorators import role_required
# Create your views here.

def signupForm(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        username   = request.POST.get('username')
        password   = request.POST.get('password')
        password2  = request.POST.get('password2')  # confirm password

        # 1️⃣ Check passwords match
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        # 2️⃣ Check if username already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('signup')

        # 3️⃣ Create the user with role
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='employee',   # default role
            is_staff=False,
            is_active=True
        )
        user.save()

        messages.success(request, 'Account created successfully! You can now log in.')
        return redirect('login')

    return render(request, 'core/signup.html')
    

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            if user.role == 'employee':
                return redirect('employee_dashboard')
            elif user.role == 'admin':
                return redirect('hr_dashboard')
        else:
         messages.error(request, 'Invalid credentials')
        return render(request, 'core/login.html')
    return render(request, 'core/login.html')  # Render the login template


def root_redirect(request):
    """
    Redirect users visiting '/' to the appropriate page.
    - Employees -> employee_dashboard
    - Admin/HR -> admin_dashboard
    - Not logged in -> login
    """
    if request.user.is_authenticated:
        if request.user.role == 'employee':
            return redirect('employee_dashboard')
        elif request.user.role == 'admin':
            return redirect('hr_dashboard')
    return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login after logout




def employee_dashboard(request):
    user = request.user

    try:
        employee = Employee.objects.get(user=user)
        employee_department = employee.department
    except Employee.DoesNotExist:
        employee = None
        employee_department = None

    departments = Department.objects.all()  # all available departments
    unread_notifications = Notification.objects.filter(user=user, read=False)
    today = timezone.now().date()
    # Check if a record already exists for this user today
    already_checked_in = Attendance.objects.filter(employee=request.user, date=today).exists()

    context = {
        'user': user,
        'employee': employee,
        'employee_department': employee_department,
        'departments': departments,
        'unread_notifications': unread_notifications,
        'already_checked_in': already_checked_in,
    }

    return render(request, 'core/employee_dashboard.html', context)


def check_in(request):
    user = request.user
    today = timezone.now().date()

    Attendance.objects.get_or_create(
        employee=user,
        date=today,
        defaults={'status': 'present'}
    )

    return redirect('employee_dashboard')


    
@role_required(['admin', 'hr'])
def hr_dashboard(request):
    # GLOBAL STATS
    total_employees = CustomUser.objects.filter(role='employee').count()
    total_departments = Department.objects.count()
    
    
    # RECENT NOTIFICATIONS (unread for admin/HR)
    unread_notifications = Notification.objects.filter(user=request.user, read=False).order_by('-created_at')[:5]
    # New Unified Way: This counts ALL pending tickets (Leaves + Complaints)
    pending_tickets_count = Ticket.objects.filter(status='pending').count()
    
    context = {
        'total_employees': total_employees,
        'total_departments': total_departments,
        'pending_tickets_count': pending_tickets_count,
        'unread_notifications': unread_notifications,
        
    }

    return render(request, 'core/hr_dashboard.html', context)


def mark_all_notifications_read(request):
    # This uses 'read' which matches your model
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return redirect(request.META.get('HTTP_REFERER', 'hr_dashboard'))


def profile_view(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'core/profile.html', context)



def update_user(request):
    if request.method == 'POST':
        user = request.user
        # Get data from the form
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        
        # Save the changes
        user.save()
        
        messages.success(request, "Your profile has been updated successfully!")
        return redirect('profile')
    
    return redirect('profile')
    
    
    
    
def feed_component(request):

    return render(request, 'core/feed_component.html')




@role_required(['admin', 'hr'])
def user_management(request):
    users = CustomUser.objects.all()
    departments = Department.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        target_user = CustomUser.objects.filter(id=user_id).first()

        # 1. CREATE USER
        if action == 'create_user':
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            role = request.POST['role']
            dept_id = request.POST.get('department')

            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
            else:
                new_user = CustomUser.objects.create_user(
                    username=username, email=email, password=password, role=role
                )
                department = Department.objects.filter(id=dept_id).first() if dept_id else None
                Employee.objects.create(user=new_user, department=department)
                messages.success(request, f'User {username} created.')

        # 2. UPDATE ROLE
        elif action == 'update_role' and target_user:
            role = request.POST.get('role')
            target_user.role = role
            target_user.save()
            messages.success(request, f'Updated role for {target_user.username}.')

        # 3. UPDATE DEPARTMENT
        elif action == 'update_department' and target_user:
            dept_id = request.POST.get('department')
            dept = Department.objects.filter(id=dept_id).first() if dept_id else None
            employee, created = Employee.objects.get_or_create(user=target_user)
            employee.department = dept
            employee.save()
            messages.success(request, f'Updated department for {target_user.username}.')

        # 4. TOGGLE STATUS
        elif action == 'toggle_approval' and target_user:
            target_user.is_active = not target_user.is_active
            target_user.save()
            messages.success(request, f'Toggled status for {target_user.username}.')

        # 5. DELETE USER (Moved this inside the POST block)
        elif action == 'delete_user':
            # Use target_user which we already looked up at the top
            if not target_user:
                messages.error(request, "User not found.")
            elif target_user == request.user:
                messages.error(request, "You cannot delete your own account.")
            else:
                username = target_user.username
                target_user.delete()
                messages.success(request, f"User '{username}' has been permanently deleted.")

        # This redirect handles all POST actions
        return redirect('user_management')

    # This handles the initial GET request to view the page
    return render(request, 'core/user_management.html', {'users': users, 'departments': departments})

@role_required(['admin', 'hr'])
def add_department(request):
    form = DepartmentForm()

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully!")
            return redirect('hr_department')  # redirect to department overview
        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, 'core/add_department.html', {'form': form})

@role_required(['admin', 'hr', 'employee'])
def department_detail(request, pk=None):
    # 1. Determine the Department
    if request.user.role in ['admin', 'hr']:
        department = get_object_or_404(Department, pk=pk)
    else: 
        if not hasattr(request.user, 'employee'):
            messages.error(request, "Employee profile not found.")
            return redirect('employee_dashboard')
        department = request.user.employee.department

    # 2. Get the People and the Work (Available to Everyone)
    employees = department.employees.all()
    tasks = Task.objects.filter(department=department).order_by('due_date')

    context = {
        'department': department,
        'employees': employees,
        'tasks': tasks,
    }

    # 3. Attendance Logic (Only for Admin/HR)
    if request.user.role in ['admin', 'hr']:
        today = timezone.now().date()
        
        # We get the User IDs from the Employee profiles in this department
        user_ids = employees.values_list('user_id', flat=True)
        
        # Filter attendance where the 'employee' field (which is a User) matches our list
        today_attendance = Attendance.objects.filter(
            date=today, 
            employee_id__in=user_ids
        )

        # Create a dictionary for quick lookup: { user_id: attendance_record }
        attendance_dict = {a.employee_id: a for a in today_attendance}

        attendance_data = []
        for emp in employees:
            record = attendance_dict.get(emp.user.id)
            
            attendance_data.append({
                'employee': emp,
                'is_present': record is not None and record.status == 'present',
                'status': record.get_status_display() if record else "Absent",
                # record.check_in_time is a TimeField, so we format it directly
                'check_in_time': record.check_in_time.strftime("%H:%M") if record and record.check_in_time else "--:--"
            })
        
        context['attendance_data'] = attendance_data

    return render(request, 'core/department_detail.html', context)

@role_required(['admin', 'hr'])
def create_task(request):
    if request.method == "POST":
        dept_id = request.POST.get('department_id')
        emp_id = request.POST.get('assigned_to')
        
        department = get_object_or_404(Department, id=dept_id)
        employee = get_object_or_404(Employee, id=emp_id)
        
        Task.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            department=department,
            assigned_to=employee,
            due_date=request.POST.get('due_date'),
            status='pending'
        )
        messages.success(request, "New task assigned successfully!")
        return redirect('department_detail', pk=dept_id)


def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Security Check: Only the assigned employee can mark it as done
    # (Or an Admin/HR)
    if task.assigned_to.user == request.user or request.user.role in ['admin', 'hr']:
        task.status = 'completed'
        task.save()
        messages.success(request, f"Task '{task.title}' marked as completed!")
    else:
        messages.error(request, "You are not authorized to complete this task.")
        
    # Redirect back to the department detail page
    return redirect('department_detail', pk=task.department.id)


@role_required(['admin', 'hr'])
def edit_department(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    
    if request.method == 'POST':
        # If you have a ModelForm, this is the easiest way:
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{department.name}' updated successfully!")
            return redirect('department_detail', pk=dept_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Pre-fill the form with existing data
        form = DepartmentForm(instance=department)
    
    return render(request, 'core/edit_department.html', {
        'form': form,
        'department': department
    })




@role_required(['admin', 'hr'])
def delete_department(request, dept_id):
    # 1. Fetch the department
    department = get_object_or_404(Department, id=dept_id)
    
    # 2. Safety: Only process if it's a POST request (from a form/modal)
    if request.method == 'POST':
        # 3. CHECK FOR EMPLOYEES
        # This prevents breaking employee profiles
        if department.employees.exists():
            count = department.employees.count()
            messages.error(request, 
                f"Action Denied: {department.name} has {count} active employees. "
                "Please reassign them to a different department before deleting."
            )
            # Redirect back to the detail page of that department
            return redirect('department_detail', pk=dept_id)

        # 4. If empty, proceed with deletion
        dept_name = department.name
        department.delete()
        messages.success(request, f"Department '{dept_name}' has been successfully removed.")
        return redirect('hr_department')

    # 5. If someone tries to visit the URL via GET, send them back
    return redirect('department_detail', pk=dept_id)




@role_required(['admin', 'hr'])  
def hr_department(request):
    # 1. Fetch the counts for the stats grid
    total_employees = Employee.objects.count()
    total_departments = Department.objects.count()
    
    # 2. Tickets (Matching your template variable names)
    pending_tickets_count = Ticket.objects.filter(status__iexact='pending').count()
    
    # 3. Notifications (Assuming you have a Notification model)
    # We filter for unread notifications for the logged-in user
    unread_notifications = Notification.objects.filter(user=request.user,read=False).order_by('-created_at')

    # 4. Departments list (if you use it elsewhere in the page)
    departments = Department.objects.all()

    context = {
        'departments': departments,
        'total_employees': total_employees,
        'total_departments': total_departments,
        'pending_tickets': pending_tickets_count, # Used in the highlight card
        'tickets': pending_tickets_count,         # Used in the stats grid
        'unread_notifications': unread_notifications,
    }

    return render(request, 'core/hr_department.html', context)





@role_required(['admin', 'hr'])
def analytics_view(request):
    today = timezone.now().date()

    # BASIC STATS
    total_employees = CustomUser.objects.count()
    active_employees = CustomUser.objects.filter(is_active=True).count()
    inactive_employees = CustomUser.objects.filter(is_active=False).count()
    total_departments = Department.objects.count()

    # EMPLOYEES PER DEPARTMENT
    # Use .values_list for a cleaner extraction
    departments = Department.objects.annotate(emp_count=Count('employees'))
    dept_names = list(departments.values_list('name', flat=True))
    dept_counts = list(departments.values_list('emp_count', flat=True))

    # ATTENDANCE TODAY
    present_count = Attendance.objects.filter(date=today).count()
    absent_count = max(0, total_employees - present_count) # Ensure it doesn't go negative

    # ATTENDANCE TREND (Last 7 or 30 days is usually better than 'all')
    attendance_trend = (
        Attendance.objects.values('date')
        .annotate(count=Count('id'))
        .order_by('date')[:30] # Limit to last 30 entries for readability
    )

    dates = [str(a['date']) for a in attendance_trend]
    counts = [a['count'] for a in attendance_trend]

    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'total_departments': total_departments,

        # Convert lists to JSON strings so JS can read them easily
        'dept_names_json': json.dumps(list(dept_names)),
        'dept_counts_json': json.dumps(list(dept_counts)),
        'present_count': present_count,
        'absent_count': absent_count,
        'dates_json': json.dumps(list(dates)),
        'counts_json': json.dumps(list(counts)),
    }

    return render(request, 'core/analytics.html', context)



    

@role_required(['employee'])
def ticket_list(request):
    # This filters by the logged-in user's employee profile instead of just status
    tickets = Ticket.objects.filter(employee__user=request.user).order_by('-created_at')
    return render(request, 'core/ticket_list.html', {'tickets': tickets})

@role_required(['admin', 'hr'])
def review_tickets(request):
    # Handle Approve/Reject POST requests
    if request.method == "POST":
        ticket_id = request.POST.get('ticket_id')
        new_status = request.POST.get('status')
        comment = request.POST.get('admin_comment', '') # Capture the comment
        ticket = Ticket.objects.get(id=ticket_id)
        ticket.status = new_status
        ticket.admin_comment = comment  # Save the admin's comment to the ticket
        ticket.save()
        messages.success(request, f"Ticket #{ticket.id} has been {new_status}.")
        
    # Show pending tickets at the top, then others
    tickets = Ticket.objects.all().order_by('status', '-created_at')
    return render(request, 'core/review_tickets.html', {'tickets': tickets})


@role_required(['employee'])
def create_ticket(request):
    if request.method == 'POST':
        # 1. Use the field names exactly as they are in your HTML form 'name' attributes
        category = request.POST.get('category') 
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        description = request.POST.get('description')

        # 2. Get the specific Employee object linked to this User
        # This prevents the "Cannot assign User to Ticket.employee" error
        employee_profile = request.user.employee 

        # 3. Create the ticket using the correct model fields
        Ticket.objects.create(
            employee=employee_profile,
            category=category,
            start_date=start_date if category == 'leave' else None,
            end_date=end_date if category == 'leave' else None,
            description=description,
            status='pending' # Always start as pending
        )
        
        messages.success(request, 'Your request has been submitted!')
        return redirect('ticket_list') # Redirect to their history list

    return render(request, 'core/create_ticket.html')


@role_required(['admin', 'hr', 'employee'])
def ticket_detail(request, ticket_id):
    # 1. Admin & HR can see everything
    if request.user.role in ['admin', 'hr']:
        ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # 2. Employees can only see their own
    else:
        ticket = get_object_or_404(Ticket, id=ticket_id, employee__user=request.user)
        
    return render(request, 'core/ticket_detail.html', {'ticket': ticket})





@role_required(['admin', 'hr', 'employee'])
def employee_attendance_log(request, employee_id):
    # 1. Get the Employee object
    employee_obj = get_object_or_404(Employee, id=employee_id)
    
    # 2. Safety Check (Prevent employees from seeing others)
    if request.user.role == 'employee' and request.user != employee_obj.user:
        messages.error(request, "Unauthorized access.")
        return redirect('employee_dashboard')

    
    
    # Use this if 'employee' is actually a link to the User account
    history = Attendance.objects.filter(employee=employee_obj.user).order_by('-date')
    
    

    clock_in_deadline = datetime.time(9, 0)
    
    return render(request, 'core/attendance_log.html', {
        'employee': employee_obj,
        'history': history,
        'clock_in_deadline': clock_in_deadline
    })