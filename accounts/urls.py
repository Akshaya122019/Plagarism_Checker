from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Template pages
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_page, name='profile'),

    # REST API endpoints
    path('api/register/', views.RegisterAPIView.as_view(), name='api-register'),
    path('api/login/', views.LoginAPIView.as_view(), name='api-login'),
    path('api/logout/', views.LogoutAPIView.as_view(), name='api-logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/profile/', views.ProfileAPIView.as_view(), name='api-profile'),
]