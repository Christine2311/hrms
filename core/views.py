import json
from django.shortcuts import render,get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout

from django.contrib import messages 

from .forms import DepartmentForm
from django.utils import timezone
from django.db.models import Count


from django.contrib.auth.hashers import make_password

from .models import CustomUser, Attendance, Ticket
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
    # This finds all unread notifications for the logged-in user and updates them
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # Redirect the user back to wherever they were
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


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
                    username=username,
                    email=email,
                    password=password,
                    role=role
                )
                department = Department.objects.filter(id=dept_id).first() if dept_id else None
                Employee.objects.create(user=new_user, department=department)
                
                messages.success(request, f'User {username} created.')

        elif action == 'update_role' and target_user:
            role = request.POST.get('role')
            target_user.role = role
            target_user.save()
            messages.success(request, f'Updated role for {target_user.username}.')

        elif action == 'update_department' and target_user:
         dept_id = request.POST.get('department')
         dept = Department.objects.filter(id=dept_id).first() if dept_id else None

    # Update or create Employee record
         employee, created = Employee.objects.get_or_create(user=target_user)
         employee.department = dept
         employee.save()

         messages.success(request, f'Updated department for {target_user.username}.')
        elif action == 'toggle_approval' and target_user:
            target_user.is_active = not target_user.is_active
            target_user.save()
            messages.success(request, f'Toggled status for {target_user.username}.')

        return redirect('user_management')

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
    # 1. Determine Department
    if request.user.role in ['admin', 'hr']:
        department = get_object_or_404(Department, pk=pk)
    else: 
        if not hasattr(request.user, 'employee'):
            messages.error(request, "Employee profile not found.")
            return redirect('employee_dashboard')
        department = request.user.employee.department

    employees = department.employees.all()
    context = {
        'department': department,
        'employees': employees,
    }

    # 2. Attendance Logic (Refined for your specific Model)
    if request.user.role in ['admin', 'hr']:
        today = timezone.now().date()
        
        # We filter based on the 'user_id' because your Attendance model 
        # links to 'User', not the 'Employee' profile.
        user_ids = employees.values_list('user_id', flat=True)
        today_attendance = Attendance.objects.filter(
            date=today, 
            employee_id__in=user_ids
        )

        # Map { User_ID : Attendance_Object }
        attendance_dict = {a.employee_id: a for a in today_attendance}

        attendance_data = []
        for emp in employees:
            # We look up the record using the ID of the User attached to the Employee
            record = attendance_dict.get(emp.user.id)
            
            attendance_data.append({
                'employee': emp,
                'is_present': record is not None,
                'status': record.get_status_display() if record else "Absent",
                # Using your actual model field name: check_in_time
                'check_in_time': record.check_in_time.strftime("%H:%M") if record else None
            })
        
        context['attendance_data'] = attendance_data

    return render(request, 'core/department_detail.html', context)

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
    departments = Department.objects.all()

    context = {
        'departments': departments
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
    tickets = Ticket.objects.filter(status='pending').order_by('-created_at')
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