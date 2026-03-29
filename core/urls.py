from django.urls import path
from . import views


urlpatterns = [
    path('', views.root_redirect, name='root_redirect'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signupForm, name='signup'),
    path('logout/', views.logout_view, name='logout'), 
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/hr/', views.hr_dashboard, name='hr_dashboard'), 
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_user, name='update_user'),
    path('feed/', views.feed_component, name='feed'),
    path('department/add/', views.add_department, name='add_department'),
    path('user-management/', views.user_management, name='user_management'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('hr/departments/', views.hr_department, name='hr_department'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    path('check-in/', views.check_in, name='check_in'),
    
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/review/', views.review_tickets, name='review_tickets'),


    path('tickets/create/', views.create_ticket, name='create_ticket'),
    
    path('ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    
    
    path('notifications/mark-read/', views.mark_all_notifications_read, name='mark_all_read'),
    path('department/edit/<int:dept_id>/', views.edit_department, name='edit_department'),
    path('department/delete/<int:dept_id>/', views.delete_department, name='delete_department'),
    
    path('attendance/history/<int:employee_id>/', views.employee_attendance_log, name='attendance_log'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('tasks/create/', views.create_task, name='create_task'),
    
]
