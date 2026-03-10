from django.urls import path
from . import views


urlpatterns = [
    path('', views.root_redirect, name='root_redirect'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signupForm, name='signup'),
    path('logout/', views.logout_view, name='logout'), 
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_user, name='update_user'),
    path('feed/', views.feed_component, name='feed'),
    path('department/add/', views.add_department, name='add_department'),
]