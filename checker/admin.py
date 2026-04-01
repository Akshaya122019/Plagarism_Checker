from django.contrib import admin
from .models import CheckResult


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'check_type',
        'similarity_percentage', 'verdict',
        'plagiarism_detected', 'created_at'
    ]
    list_filter = ['verdict', 'check_type', 'plagiarism_detected']
    search_fields = ['user__username', 'original_text']
    readonly_fields = ['created_at']
    ordering = ['-created_at']