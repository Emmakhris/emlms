from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_successful_payment(self, order_id):
    """After payment: create enrollment, progress record, notification, send email."""
    try:
        from .models import Order
        from apps.enrollments.models import Enrollment, CourseProgress
        from apps.core.models import Notification

        order = Order.objects.select_related('student', 'course', 'coupon').get(id=order_id)

        enrollment, created = Enrollment.objects.get_or_create(
            student=order.student,
            course=order.course,
            defaults={
                'status': 'active',
                'amount_paid': order.final_amount,
                'coupon_used': order.coupon,
            }
        )

        if created:
            CourseProgress.objects.get_or_create(
                enrollment=enrollment,
                defaults={'total_lessons': order.course.total_lessons}
            )
            order.course.total_enrolled = order.course.enrollments.filter(status='active').count()
            order.course.save(update_fields=['total_enrolled'])

            if order.coupon:
                order.coupon.usage_count += 1
                order.coupon.save(update_fields=['usage_count'])
                from apps.coupons.models import CouponUsage
                CouponUsage.objects.get_or_create(
                    coupon=order.coupon,
                    user=order.student,
                    order=order,
                    defaults={'discount_given': order.discount_amount},
                )

            Notification.objects.create(
                user=order.student,
                notif_type='enrollment',
                title=f'Enrolled: {order.course.title}',
                message='You now have full access to this course.',
                link=f'/courses/{order.course.slug}/learn/',
            )

            send_enrollment_email.delay(str(enrollment.id))
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_enrollment_email(self, enrollment_id):
    try:
        from apps.enrollments.models import Enrollment
        from django.core.mail import send_mail
        from django.conf import settings

        enrollment = Enrollment.objects.select_related('student', 'course').get(id=enrollment_id)
        student = enrollment.student
        course = enrollment.course

        send_mail(
            subject=f'You are enrolled in {course.title}',
            message=f'Hi {student.first_name},\n\nYou are now enrolled in "{course.title}".\n\nStart learning: {settings.SITE_URL}/courses/{course.slug}/learn/',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)
