from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout
from django.shortcuts import redirect
from django.contrib import messages 

from .models import CustomUser
from .models import Department
from .decorators import role_required
# Create your views here.

def signupForm(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST.get('username')
        password = request.POST.get('password')
      
       # Check if the username already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('signup')

        # Create the user
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='employee',
            is_staff=False,  # prevents them from going to admin
            is_active=True
        )
        user.save()

        messages.success(request, 'Account created successfully! You can now log in.')
        return redirect('login')  # Redirect to login after signup
    return render(request, 'core/signup.html')  # Render the signup template
    

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
                return redirect('admin_dashboard')
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
            return redirect('admin_dashboard')
    return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login after logout

@role_required(['employee'])
def employee_dashboard(request):
    departments = Department.objects.all()
    user_department = request.user.department
    context = { 'departments': departments, 'user_department': user_department }
    return render(request, 'core/employee_dashboard.html', context)
    
    
def admin_dashboard(request):
    return HttpResponse("Admin Dashboard - Under Construction")



def profile_view(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'core/profile.html', context)

def update_user(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        # Add more fields as needed
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    else:
        return redirect('profile')
    
    
def feed_component(request):

    return render(request, 'core/feed_component.html')

def add_department(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            Department.objects.create(name=name, description=description)
            messages.success(request, 'Department added successfully!')
            return redirect('employee_dashboard')
        else:
            messages.error(request, 'Department name is required.')
    return render(request, 'core/add_department.html')