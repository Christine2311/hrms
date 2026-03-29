from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps # Add this import

def role_required(required_roles):
    def decorator(view_func):
        @wraps(view_func) # Add this to preserve view metadata
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in first.")
                return redirect('login')

            if not hasattr(request.user, 'role'):
                messages.error(request, "User role not defined.")
                return redirect('login')

            if request.user.role not in required_roles:
                messages.error(request, "You are not authorized to access this page.")
                # Suggestion: Redirect to 'dashboard' instead of 'login' 
                # so they don't have to keep logging back in!
                return redirect('hr_dashboard') 

            # CRITICAL: Pass *args and **kwargs here!
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator