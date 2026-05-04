import shortuuid
from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_and_issue_certificate(self, enrollment_id):
    """Check if course is 100% complete and issue certificate if so."""
    from celery.exceptions import Retry
    try:
        from apps.enrollments.models import Enrollment, CourseProgress
        from apps.courses.models import Course

        enrollment = Enrollment.objects.select_related('student', 'course__instructor').get(id=enrollment_id)
        course = enrollment.course

        if not course.certificate_enabled:
            return

        # Check if certificate already issued
        if hasattr(enrollment, 'certificate'):
            return

        # Verify 100% completion
        progress = getattr(enrollment, 'progress', None)
        if not progress or progress.percentage < 100:
            return

        # Issue certificate
        verification_code = f'EMLMS-{shortuuid.uuid()[:8].upper()}'

        from .models import Certificate
        from django.utils.timezone import now

        cert = Certificate.objects.create(
            enrollment=enrollment,
            student=enrollment.student,
            course=course,
            verification_code=verification_code,
            student_name=enrollment.student.get_full_name(),
            course_title=course.title,
            instructor_name=course.instructor.get_full_name(),
            completion_date=now().date(),
            course_duration_hours=round(course.total_duration_minutes / 60, 1),
        )

        # Update enrollment status
        enrollment.status = 'completed'
        enrollment.completed_at = now()
        enrollment.save()

        # Generate PDF (best-effort; may not be available in dev)
        try:
            generate_certificate_pdf.delay(str(cert.id))
        except (Retry, Exception):
            pass

        # Notify student
        from apps.core.models import Notification
        Notification.objects.create(
            user=enrollment.student,
            notif_type='certificate',
            title=f'Certificate Earned: {course.title}',
            message='Congratulations! Your certificate is ready.',
            link=cert.get_absolute_url(),
        )

    except (Retry, Exception) as exc:
        if isinstance(exc, Retry):
            raise
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_certificate_pdf(self, certificate_id):
    """Render HTML certificate to PDF using WeasyPrint."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        import weasyprint
    except (ImportError, OSError) as exc:
        logger.warning('WeasyPrint not available (missing system libs): %s', exc)
        return  # PDF generation skipped; certificate record still exists

    try:
        from io import BytesIO
        from django.template.loader import render_to_string
        from django.core.files.base import ContentFile

        from .models import Certificate
        cert = Certificate.objects.select_related('student', 'course', 'course__instructor').get(id=certificate_id)

        import qrcode
        import base64
        from io import BytesIO as IOBytes
        from django.conf import settings

        qr_url = f'{settings.SITE_URL}/certificates/verify/{cert.verification_code}/'
        qr_img = qrcode.make(qr_url)
        qr_buffer = IOBytes()
        qr_img.save(qr_buffer, format='PNG')
        qr_b64 = base64.b64encode(qr_buffer.getvalue()).decode()

        html_string = render_to_string('certificates/pdf_template.html', {
            'cert': cert,
            'qr_code_b64': qr_b64,
            'verify_url': qr_url,
        })

        pdf_bytes = weasyprint.HTML(string=html_string).write_pdf()
        cert.pdf_file.save(f'cert_{cert.id}.pdf', ContentFile(pdf_bytes))

        send_certificate_email.delay(str(cert.id))

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_certificate_email(self, certificate_id):
    try:
        from .models import Certificate
        from django.core.mail import EmailMessage
        from django.conf import settings

        cert = Certificate.objects.select_related('student', 'course').get(id=certificate_id)
        student = cert.student

        email = EmailMessage(
            subject=f'Your Certificate for {cert.course_title}',
            body=f'Hi {student.first_name},\n\nCongratulations on completing "{cert.course_title}"!\n\nView your certificate: {settings.SITE_URL}{cert.get_absolute_url()}\n\nVerification code: {cert.verification_code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[student.email],
        )

        if cert.pdf_file:
            email.attach(f'certificate-{cert.course_title}.pdf', cert.pdf_file.read(), 'application/pdf')

        email.send()
    except Exception as exc:
        raise self.retry(exc=exc)
