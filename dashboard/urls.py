from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.dashboard_home,  name='dashboard'),
    path('stats/',                  views.dashboard_stats, name='dashboard-stats'),
    path('users/',                  views.users_page,      name='dashboard-users'),
    path('users/data/',             views.users_data,      name='dashboard-users-data'),
    path('users/toggle/<int:user_id>/', views.toggle_user, name='dashboard-toggle-user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='dashboard-delete-user'),
    path('checks/',                 views.checks_page,     name='dashboard-checks'),
    path('checks/data/',            views.checks_data,     name='dashboard-checks-data'),
    path('checks/delete/<int:check_id>/', views.delete_check, name='dashboard-delete-check'),
]