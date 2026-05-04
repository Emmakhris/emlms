from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone

from apps.core.mixins import EnrollmentRequiredMixin
from apps.enrollments.models import Enrollment, CourseProgress
from .models import Lesson, LessonProgress, Section
from apps.courses.models import Course


@login_required
def course_learn(request, course_slug, lesson_id=None):
    """Main lesson player view — renders the full course learning interface."""
    course = get_object_or_404(Course, slug=course_slug, status='published')

    # Access control
    is_instructor = request.user.is_instructor and course.instructor == request.user
    enrollment = None
    if not is_instructor:
        enrollment = get_object_or_404(Enrollment, student=request.user, course=course, status='active')

    # Get sections with lessons
    sections = Section.objects.filter(course=course).prefetch_related('lessons').order_by('order')

    # Determine current lesson
    if lesson_id:
        lesson = get_object_or_404(Lesson, id=lesson_id, section__course=course, is_published=True)
    else:
        # Resume from last accessed or first lesson
        if enrollment:
            progress = getattr(enrollment, 'progress', None)
            if progress and progress.last_accessed_lesson:
                lesson = progress.last_accessed_lesson
            else:
                first_section = sections.first()
                lesson = first_section.lessons.filter(is_published=True).first() if first_section else None
        else:
            first_section = sections.first()
            lesson = first_section.lessons.filter(is_published=True).first() if first_section else None

    # Get lesson progress for the student
    progress_map = {}
    if request.user.is_authenticated and enrollment:
        for lp in LessonProgress.objects.filter(student=request.user, lesson__section__course=course):
            progress_map[str(lp.lesson_id)] = lp

    # Update last accessed lesson
    if enrollment and lesson:
        CourseProgress.objects.filter(enrollment=enrollment).update(
            last_accessed_lesson=lesson,
            last_accessed_at=timezone.now()
        )

    # Get lesson-specific content
    lesson_content = None
    if lesson:
        if lesson.lesson_type == 'video' and hasattr(lesson, 'video'):
            lesson_content = lesson.video
        elif lesson.lesson_type == 'text' and hasattr(lesson, 'text'):
            lesson_content = lesson.text
        elif lesson.lesson_type == 'quiz' and hasattr(lesson, 'quiz'):
            lesson_content = lesson.quiz
        elif lesson.lesson_type == 'resource':
            lesson_content = lesson.resources.all()

    current_lesson_progress = progress_map.get(str(lesson.id)) if lesson else None
    completed_lesson_ids = {
        lp.lesson_id for lp in progress_map.values() if lp.status == 'completed'
    }
    is_lesson_completed = bool(
        current_lesson_progress and current_lesson_progress.status == 'completed'
    )

    context = {
        'course': course,
        'sections': sections,
        'lesson': lesson,
        'lesson_content': lesson_content,
        'progress_map': progress_map,
        'current_lesson_progress': current_lesson_progress,
        'completed_lesson_ids': completed_lesson_ids,
        'is_lesson_completed': is_lesson_completed,
        'enrollment': enrollment,
        'is_instructor': is_instructor,
    }
    return render(request, 'lessons/course_learn.html', context)


@login_required
@require_POST
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.section.course

    # Verify enrollment
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course, status='active')

    lp, _ = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
    lp.mark_complete()

    # Update course progress
    _update_course_progress(enrollment)

    if request.htmx:
        return render(request, 'lessons/partials/lesson_complete_btn.html', {'lesson': lesson, 'completed': True})
    return JsonResponse({'status': 'completed'})


@login_required
@require_POST
def save_video_progress(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, lesson_type='video')
    try:
        position = int(request.POST.get('position', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'invalid position'}, status=400)

    lp, _ = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
    lp.last_position_seconds = position
    if lp.status == 'not_started':
        lp.status = 'in_progress'

    # Auto-complete at 90% watched
    if hasattr(lesson, 'video') and lesson.video.duration_seconds > 0:
        if position / lesson.video.duration_seconds > 0.9:
            lp.mark_complete()
            enrollment = Enrollment.objects.filter(student=request.user, course=lesson.section.course, status='active').first()
            if enrollment:
                _update_course_progress(enrollment)
    lp.save()
    return JsonResponse({'status': 'ok'})


def _update_course_progress(enrollment):
    """Recalculate and save course progress percentage."""
    total = enrollment.course.total_lessons
    completed = LessonProgress.objects.filter(
        student=enrollment.student,
        lesson__section__course=enrollment.course,
        status='completed'
    ).count()

    percentage = (completed / total * 100) if total > 0 else 0

    progress, _ = CourseProgress.objects.get_or_create(enrollment=enrollment)
    progress.lessons_completed = completed
    progress.total_lessons = total
    progress.percentage = percentage
    progress.save()

    # Trigger certificate if 100%
    if percentage >= 100:
        from apps.certificates.tasks import check_and_issue_certificate
        check_and_issue_certificate.delay(str(enrollment.id))
