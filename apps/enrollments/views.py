from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.courses.models import Course
from .models import Enrollment, CourseProgress


@login_required
def enroll_free(request, slug):
    """Enroll in a free course directly."""
    course = get_object_or_404(Course, slug=slug, status='published', pricing_type='free')

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('lessons:learn', course_slug=slug)

    enrollment = Enrollment.objects.create(
        student=request.user,
        course=course,
        status='active',
        amount_paid=0,
    )
    CourseProgress.objects.create(
        enrollment=enrollment,
        total_lessons=course.total_lessons,
    )
    course.total_enrolled += 1
    course.save(update_fields=['total_enrolled'])

    messages.success(request, f'You are now enrolled in "{course.title}"!')
    return redirect('lessons:learn', course_slug=slug)


@login_required
def my_courses(request):
    enrollments = Enrollment.objects.filter(
        student=request.user, status__in=['active', 'completed']
    ).select_related('course', 'course__instructor', 'progress').order_by('-enrolled_at')

    return render(request, 'enrollments/my_courses.html', {'enrollments': enrollments})
