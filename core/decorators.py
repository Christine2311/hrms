from django.shortcuts import redirect
from django.contrib import messages

def role_required(required_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in first.")
                return redirect('login')

            if not hasattr(request.user, 'role'):
                messages.error(request, "User role not defined.")
                return redirect('login')

            if request.user.role not in required_roles:
                messages.error(request, "You are not authorized to access this page.")
                return redirect('login')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
