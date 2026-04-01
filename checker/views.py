from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import CheckResult
from .serializers import (
    CheckResultSerializer,
    TextCheckSerializer,
    WebCheckSerializer,
    FileCheckSerializer,
)
from .engine import compute_similarity, extract_keywords, compare_against_sources
from .extractor import extract_text_from_file
from .scraper import scrape_sources


# ── API: Text vs Text ────────────────────────────────────────
class TextCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TextCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        text1 = serializer.validated_data['text1']
        text2 = serializer.validated_data['text2']

        # Run similarity engine
        result = compute_similarity(text1, text2)

        # Save to database
        check = CheckResult.objects.create(
            user=request.user,
            check_type='text',
            original_text=text1,
            compare_text=text2,
            similarity_percentage=result['similarity_percentage'],
            verdict=result['verdict'],
            plagiarism_detected=result['plagiarism_detected'],
            matched_sentences=result['matched_sentences'],
            source_results=[],
        )

        return Response({
            'check_id': check.id,
            'check_type': 'text',
            'similarity_percentage': result['similarity_percentage'],
            'verdict': result['verdict'],
            'plagiarism_detected': result['plagiarism_detected'],
            'matched_sentences': result['matched_sentences'],
        }, status=status.HTTP_200_OK)


# ── API: Text vs Web ─────────────────────────────────────────
class WebCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WebCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        text = serializer.validated_data['text']
        num_sources = serializer.validated_data['num_sources']

        # Extract keywords for Google search
        query = extract_keywords(text, num=8)

        # Scrape web sources
        sources = scrape_sources(query, num_results=num_sources)

        if not sources:
            return Response({
                'error': 'Could not fetch web sources. Try again later.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Compare against all sources
        result = compare_against_sources(text, sources)

        # Save to database
        check = CheckResult.objects.create(
            user=request.user,
            check_type='web',
            original_text=text,
            compare_text='',
            similarity_percentage=result['overall_similarity'],
            verdict=result['verdict'],
            plagiarism_detected=result['plagiarism_detected'],
            matched_sentences=result['all_matched_sentences'],
            source_results=result['source_results'],
        )

        return Response({
            'check_id': check.id,
            'check_type': 'web',
            'similarity_percentage': result['overall_similarity'],
            'verdict': result['verdict'],
            'plagiarism_detected': result['plagiarism_detected'],
            'highest_source': result['highest_source'],
            'sources_checked': len(sources),
            'source_results': result['source_results'],
            'matched_sentences': result['all_matched_sentences'],
        }, status=status.HTTP_200_OK)


# ── API: File vs Web ─────────────────────────────────────────
class FileCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FileCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = serializer.validated_data['file']
        num_sources = serializer.validated_data['num_sources']

        # Extract text from file
        try:
            text = extract_text_from_file(uploaded_file)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(text.strip()) < 50:
            return Response(
                {'error': 'File content too short to check.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract keywords and search web
        query = extract_keywords(text, num=8)
        sources = scrape_sources(query, num_results=num_sources)

        if not sources:
            return Response({
                'error': 'Could not fetch web sources. Try again later.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Compare
        result = compare_against_sources(text, sources)

        # Reset file pointer before saving
        uploaded_file.seek(0)

        # Save to database
        check = CheckResult.objects.create(
            user=request.user,
            check_type='file',
            original_text=text[:5000],
            compare_text='',
            uploaded_file=uploaded_file,
            similarity_percentage=result['overall_similarity'],
            verdict=result['verdict'],
            plagiarism_detected=result['plagiarism_detected'],
            matched_sentences=result['all_matched_sentences'],
            source_results=result['source_results'],
        )

        return Response({
            'check_id': check.id,
            'check_type': 'file',
            'filename': uploaded_file.name,
            'similarity_percentage': result['overall_similarity'],
            'verdict': result['verdict'],
            'plagiarism_detected': result['plagiarism_detected'],
            'highest_source': result['highest_source'],
            'sources_checked': len(sources),
            'source_results': result['source_results'],
            'matched_sentences': result['all_matched_sentences'],
        }, status=status.HTTP_200_OK)


# ── API: History list ────────────────────────────────────────
class HistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        checks = CheckResult.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]

        serializer = CheckResultSerializer(checks, many=True)
        return Response(serializer.data)


# ── API: Single result detail ────────────────────────────────
class ResultDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        check = get_object_or_404(
            CheckResult, pk=pk, user=request.user
        )
        serializer = CheckResultSerializer(check)
        return Response(serializer.data)

    def delete(self, request, pk):
        check = get_object_or_404(
            CheckResult, pk=pk, user=request.user
        )
        check.delete()
        return Response(
            {'message': 'Result deleted.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ── Template views ───────────────────────────────────────────
@login_required
def checker_page(request):
    return render(request, 'checker/checker.html')


@login_required
def history_page(request):
    return render(request, 'checker/history.html')


@login_required
def result_page(request, pk):
    return render(request, 'checker/result.html', {'check_id': pk})

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('/checker/')
    return redirect('/accounts/login/')