from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from checker.models import CheckResult


def is_admin(user):
    return user.is_authenticated and user.is_staff


# ── Dashboard home ───────────────────────────────────────────
@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def dashboard_home(request):
    return render(request, 'dashboard/home.html')


# ── Dashboard stats API ──────────────────────────────────────
@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def dashboard_stats(request):
    now = timezone.now()
    last_30 = now - timedelta(days=30)
    last_7  = now - timedelta(days=7)

    total_users   = User.objects.filter(is_staff=False).count()
    total_checks  = CheckResult.objects.count()
    checks_today  = CheckResult.objects.filter(created_at__date=now.date()).count()
    checks_week   = CheckResult.objects.filter(created_at__gte=last_7).count()
    avg_similarity = CheckResult.objects.aggregate(a=Avg('similarity_percentage'))['a'] or 0
    plagiarism_found = CheckResult.objects.filter(plagiarism_detected=True).count()

    # Verdict breakdown
    verdict_data = (
        CheckResult.objects
        .values('verdict')
        .annotate(count=Count('id'))
        .order_by('verdict')
    )

    # Check type breakdown
    type_data = (
        CheckResult.objects
        .values('check_type')
        .annotate(count=Count('id'))
    )

    # Daily checks — last 30 days
    daily_checks = (
        CheckResult.objects
        .filter(created_at__gte=last_30)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # New users — last 30 days
    new_users = (
        User.objects
        .filter(date_joined__gte=last_30, is_staff=False)
        .annotate(date=TruncDate('date_joined'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Recent checks
    recent_checks = (
        CheckResult.objects
        .select_related('user')
        .order_by('-created_at')[:10]
    )
    recent_list = [{
        'id':         c.id,
        'username':   c.user.username,
        'check_type': c.check_type,
        'similarity': c.similarity_percentage,
        'verdict':    c.verdict,
        'created_at': c.created_at.strftime('%d %b %Y, %I:%M %p'),
    } for c in recent_checks]

    return JsonResponse({
        'summary': {
            'total_users':      total_users,
            'total_checks':     total_checks,
            'checks_today':     checks_today,
            'checks_week':      checks_week,
            'avg_similarity':   round(avg_similarity, 1),
            'plagiarism_found': plagiarism_found,
        },
        'verdict_data': list(verdict_data),
        'type_data':    list(type_data),
        'daily_checks': [
            {'date': str(d['date']), 'count': d['count']}
            for d in daily_checks
        ],
        'new_users': [
            {'date': str(d['date']), 'count': d['count']}
            for d in new_users
        ],
        'recent_checks': recent_list,
    })


# ── Users list ───────────────────────────────────────────────
@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def users_page(request):
    return render(request, 'dashboard/users.html')


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def users_data(request):
    users = (
        User.objects
        .filter(is_staff=False)
        .annotate(total_checks=Count('check_results'))
        .order_by('-date_joined')
    )
    data = [{
        'id':           u.id,
        'username':     u.username,
        'email':        u.email,
        'full_name':    u.get_full_name() or '—',
        'total_checks': u.total_checks,
        'is_active':    u.is_active,
        'date_joined':  u.date_joined.strftime('%d %b %Y'),
    } for u in users]
    return JsonResponse({'users': data})


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def toggle_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id, is_staff=False)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({
            'success':   True,
            'is_active': user.is_active,
        })
    return JsonResponse({'success': False}, status=405)


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id, is_staff=False)
        user.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


# ── All checks list ──────────────────────────────────────────
@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def checks_page(request):
    return render(request, 'dashboard/checks.html')


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def checks_data(request):
    checks = (
        CheckResult.objects
        .select_related('user')
        .order_by('-created_at')[:200]
    )
    data = [{
        'id':         c.id,
        'username':   c.user.username,
        'check_type': c.check_type,
        'similarity': c.similarity_percentage,
        'verdict':    c.verdict,
        'plagiarism': c.plagiarism_detected,
        'created_at': c.created_at.strftime('%d %b %Y, %I:%M %p'),
    } for c in checks]
    return JsonResponse({'checks': data})


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def delete_check(request, check_id):
    if request.method == 'POST':
        check = get_object_or_404(CheckResult, pk=check_id)
        check.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)