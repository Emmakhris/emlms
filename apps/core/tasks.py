from celery import shared_task


@shared_task
def check_course_completions():
    """Hourly: find enrollments at 100% that haven't been marked completed yet."""
    from apps.enrollments.models import Enrollment, CourseProgress
    from apps.certificates.tasks import check_and_issue_certificate

    incomplete_enrollments = Enrollment.objects.filter(
        status='active',
        progress__percentage__gte=100,
    ).values_list('id', flat=True)

    for enrollment_id in incomplete_enrollments:
        check_and_issue_certificate.delay(str(enrollment_id))


@shared_task
def update_course_statistics():
    """Nightly: recalculate total_enrolled on all published courses."""
    from django.db.models import Count
    from apps.courses.models import Course
    from apps.enrollments.models import Enrollment

    for course in Course.objects.filter(status='published').only('id'):
        count = Enrollment.objects.filter(
            course=course, status__in=['active', 'completed']
        ).count()
        Course.objects.filter(pk=course.pk).update(total_enrolled=count)


@shared_task
def send_weekly_progress_digest():
    """Sunday 8am: email each active student a summary of their weekly progress."""
    from django.utils import timezone
    from django.core.mail import send_mail
    from django.conf import settings
    from apps.accounts.models import User
    from apps.enrollments.models import Enrollment
    from apps.lessons.models import LessonProgress

    one_week_ago = timezone.now() - timezone.timedelta(days=7)

    for user in User.objects.filter(is_active=True, is_student=True).iterator():
        lessons_this_week = LessonProgress.objects.filter(
            student=user,
            status='completed',
            completed_at__gte=one_week_ago,
        ).count()

        if lessons_this_week == 0:
            continue

        active_courses = Enrollment.objects.filter(
            student=user, status='active'
        ).count()

        body = (
            f'Hi {user.first_name},\n\n'
            f'Great work this week! Here\'s your progress summary:\n\n'
            f'  Lessons completed this week: {lessons_this_week}\n'
            f'  Active courses: {active_courses}\n\n'
            f'Keep it up — log in to continue learning:\n'
            f'{settings.SITE_URL}/dashboard/\n\n'
            f'The EMLMS Team'
        )

        try:
            send_mail(
                subject='Your weekly learning progress',
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass
