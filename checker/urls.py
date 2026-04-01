from django.urls import path
from . import views

urlpatterns = [
    # Template pages
    path('', views.checker_page, name='checker'),
    path('history/', views.history_page, name='history'),
    path('result/<int:pk>/', views.result_page, name='result'),

    # REST API endpoints
    path('api/check/text/', views.TextCheckAPIView.as_view(), name='api-text-check'),
    path('api/check/web/', views.WebCheckAPIView.as_view(), name='api-web-check'),
    path('api/check/file/', views.FileCheckAPIView.as_view(), name='api-file-check'),
    path('api/history/', views.HistoryAPIView.as_view(), name='api-history'),
    path('api/result/<int:pk>/', views.ResultDetailAPIView.as_view(), name='api-result'),
]