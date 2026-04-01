from django.db import models
from django.contrib.auth.models import User


class CheckResult(models.Model):

    VERDICT_CHOICES = [
        ('clean', 'Clean'),
        ('low', 'Low Plagiarism'),
        ('medium', 'Medium Plagiarism'),
        ('high', 'High Plagiarism'),
    ]

    CHECK_TYPE_CHOICES = [
        ('text', 'Text vs Text'),
        ('web', 'Text vs Web'),
        ('file', 'File vs Web'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='check_results'
    )
    check_type = models.CharField(max_length=10, choices=CHECK_TYPE_CHOICES, default='text')

    # Input
    original_text = models.TextField()
    compare_text = models.TextField(blank=True)
    uploaded_file = models.FileField(upload_to='uploads/%Y/%m/', blank=True, null=True)

    # Results
    similarity_percentage = models.FloatField(default=0.0)
    verdict = models.CharField(max_length=10, choices=VERDICT_CHOICES, default='clean')
    plagiarism_detected = models.BooleanField(default=False)
    matched_sentences = models.JSONField(default=list)
    source_results = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.verdict} | {self.similarity_percentage}%"

    @property
    def verdict_color(self):
        colors = {
            'clean': 'success',
            'low': 'warning',
            'medium': 'orange',
            'high': 'danger',
        }
        return colors.get(self.verdict, 'secondary')