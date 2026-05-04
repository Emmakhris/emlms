from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg

from apps.enrollments.models import Enrollment
from apps.certificates.models import Certificate
from apps.core.models import ActivityLog


@login_required
def student_dashboard(request):
    user = request.user

    enrollments = Enrollment.objects.filter(
        student=user, status__in=['active', 'completed']
    ).select_related('course', 'course__instructor', 'progress').order_by('-enrolled_at')[:6]

    completed_count = Enrollment.objects.filter(student=user, status='completed').count()
    in_progress_count = Enrollment.objects.filter(student=user, status='active').count()
    certificate_count = Certificate.objects.filter(student=user, is_valid=True).count()

    recent_certs = Certificate.objects.filter(student=user, is_valid=True).select_related('course').order_by('-issued_at')[:3]
    recent_activity = ActivityLog.objects.filter(user=user).select_related()[:10]

    profile = getattr(user, 'student_profile', None)

    context = {
        'enrollments': enrollments,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'certificate_count': certificate_count,
        'recent_certs': recent_certs,
        'recent_activity': recent_activity,
        'profile': profile,
    }
    return render(request, 'dashboard/student_dashboard.html', context)


@login_required
def instructor_dashboard(request):
    if not request.user.is_instructor:
        from django.shortcuts import redirect
        return redirect('dashboard:student')

    user = request.user
    from apps.courses.models import Course

    courses = Course.objects.filter(instructor=user).annotate(
        enrollment_count=Count('enrollments'),
    ).order_by('-created_at')

    total_students = Enrollment.objects.filter(
        course__instructor=user, status__in=['active', 'completed']
    ).values('student').distinct().count()

    total_revenue = Enrollment.objects.filter(
        course__instructor=user
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    avg_rating = Course.objects.filter(instructor=user, status='published').aggregate(avg=Avg('average_rating'))['avg'] or 0

    context = {
        'courses': courses,
        'total_students': total_students,
        'total_revenue': total_revenue,
        'avg_rating': round(avg_rating, 2),
    }
    return render(request, 'dashboard/instructor_dashboard.html', context)
