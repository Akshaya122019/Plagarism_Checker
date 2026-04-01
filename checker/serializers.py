from rest_framework import serializers
from .models import CheckResult


class CheckResultSerializer(serializers.ModelSerializer):
    verdict_display = serializers.CharField(
        source='get_verdict_display', read_only=True
    )
    username = serializers.CharField(
        source='user.username', read_only=True
    )

    class Meta:
        model = CheckResult
        fields = [
            'id', 'username', 'check_type',
            'original_text', 'compare_text',
            'uploaded_file', 'similarity_percentage',
            'verdict', 'verdict_display', 'plagiarism_detected',
            'matched_sentences', 'source_results', 'created_at',
        ]
        read_only_fields = [
            'id', 'username', 'similarity_percentage', 'verdict',
            'verdict_display', 'plagiarism_detected',
            'matched_sentences', 'source_results', 'created_at',
        ]


class TextCheckSerializer(serializers.Serializer):
    """For text vs text comparison."""
    text1 = serializers.CharField(min_length=50, max_length=50000)
    text2 = serializers.CharField(min_length=50, max_length=50000)


class WebCheckSerializer(serializers.Serializer):
    """For text vs live web comparison."""
    text = serializers.CharField(min_length=50, max_length=50000)
    num_sources = serializers.IntegerField(
        min_value=1, max_value=10, default=5
    )


class FileCheckSerializer(serializers.Serializer):
    """For uploaded file vs live web comparison."""
    file = serializers.FileField()
    num_sources = serializers.IntegerField(
        min_value=1, max_value=10, default=5
    )

    def validate_file(self, value):
        allowed = ['.pdf', '.docx', '.txt']
        ext = '.' + value.name.split('.')[-1].lower()
        if ext not in allowed:
            raise serializers.ValidationError(
                'Only PDF, DOCX and TXT files are allowed.'
            )
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError(
                'File size must be under 5MB.'
            )
        return value