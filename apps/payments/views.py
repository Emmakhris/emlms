import hashlib
import hmac
import json
import uuid

from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.courses.models import Course
from apps.coupons.models import Coupon
from .models import Order, PaymentTransaction
from .paystack import PaystackService
from .tasks import process_successful_payment


@login_required
def checkout(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published', pricing_type='paid')

    # Redirect if already enrolled
    from apps.enrollments.models import Enrollment
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('lessons:learn', course_slug=slug)

    context = {
        'course': course,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    }
    return render(request, 'payments/checkout.html', context)


@login_required
@ratelimit(key='user', rate='10/m', method='POST', block=True)
def initialize_payment(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published', pricing_type='paid')

    coupon_code = request.POST.get('coupon_code', '').strip().upper()
    coupon = None
    discount_amount = 0
    original_price = course.effective_price

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            is_valid, msg = coupon.is_valid(user=request.user, course=course, amount=float(original_price))
            if is_valid:
                discount_amount = coupon.calculate_discount(original_price)
            else:
                messages.warning(request, msg)
                coupon = None
        except Coupon.DoesNotExist:
            messages.warning(request, 'Invalid coupon code.')

    final_amount = max(0, original_price - discount_amount)

    if final_amount == 0:
        # Full discount — enroll directly
        from apps.enrollments.models import Enrollment, CourseProgress
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user, course=course,
            defaults={'status': 'active', 'amount_paid': 0, 'coupon_used': coupon}
        )
        if created:
            CourseProgress.objects.create(enrollment=enrollment, total_lessons=course.total_lessons)
            if coupon:
                coupon.usage_count += 1
                coupon.save(update_fields=['usage_count'])
        messages.success(request, f'Enrolled in "{course.title}" for free with your coupon!')
        return redirect('lessons:learn', course_slug=slug)

    # Create order
    reference = f'EMLMS-{uuid.uuid4().hex[:16].upper()}'
    order = Order.objects.create(
        reference=reference,
        student=request.user,
        course=course,
        coupon=coupon,
        original_price=original_price,
        discount_amount=discount_amount,
        final_amount=final_amount,
        currency='GHS',
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    # Amount in pesewas (smallest GHS unit = 1/100 = pesewas)
    amount_kobo = int(final_amount * 100)

    callback_url = request.build_absolute_uri(f'/payments/verify/?reference={reference}')

    paystack = PaystackService()
    try:
        result = paystack.initialize_transaction(
            email=request.user.email,
            amount_kobo=amount_kobo,
            reference=reference,
            callback_url=callback_url,
            metadata={
                'order_id': str(order.id),
                'course_id': str(course.id),
                'student_id': str(request.user.id),
                'course_title': course.title,
            }
        )
        return redirect(result['data']['authorization_url'])
    except Exception as e:
        order.status = 'failed'
        order.save()
        messages.error(request, 'Payment initialization failed. Please try again.')
        return redirect('checkout:checkout', slug=slug)


def verify_payment(request):
    reference = request.GET.get('reference', '')
    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('core:home')

    order = get_object_or_404(Order, reference=reference, student=request.user)

    if order.status == 'completed':
        messages.info(request, 'This payment was already processed.')
        return redirect('lessons:learn', course_slug=order.course.slug)

    paystack = PaystackService()
    try:
        result = paystack.verify_transaction(reference)
        data = result.get('data', {})

        if data.get('status') == 'success':
            expected_kobo = int(order.final_amount * 100)
            actual_kobo = data.get('amount', 0)

            if actual_kobo < expected_kobo:
                order.status = 'failed'
                order.save()
                messages.error(request, 'Payment amount mismatch. Please contact support.')
                return redirect('core:home')

            order.status = 'completed'
            order.paystack_transaction_id = str(data.get('id', ''))
            order.payment_method = data.get('channel', '')
            order.save()

            PaymentTransaction.objects.create(
                order=order,
                paystack_reference=reference,
                paystack_transaction_id=str(data.get('id', '')),
                amount_kobo=actual_kobo,
                currency=data.get('currency', 'GHS'),
                status=data.get('status', ''),
                gateway_response=data.get('gateway_response', ''),
                channel=data.get('channel', ''),
                raw_response=data,
                paid_at=parse_datetime(data['paid_at']) if data.get('paid_at') else None,
            )

            process_successful_payment.delay(str(order.id))
            messages.success(request, f'Payment successful! You are now enrolled in "{order.course.title}".')
            return redirect('lessons:learn', course_slug=order.course.slug)
        else:
            order.status = 'failed'
            order.save()
            messages.error(request, 'Payment was not successful. Please try again.')
            return redirect('checkout:checkout', slug=order.course.slug)

    except Exception:
        messages.error(request, 'Could not verify payment. Please contact support with your reference.')
        return redirect('core:home')


@csrf_exempt
@require_POST
def paystack_webhook(request):
    """Async backup verification — idempotent, HMAC-validated."""
    paystack_secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
    signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
    body = request.body

    computed = hmac.new(paystack_secret, body, digestmod=hashlib.sha512).hexdigest()
    if not hmac.compare_digest(computed, signature):
        return HttpResponse(status=400)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    event = payload.get('event')
    if event == 'charge.success':
        reference = payload['data'].get('reference', '')
        try:
            order = Order.objects.get(reference=reference)
            if order.status != 'completed':
                order.status = 'completed'
                order.save()
                process_successful_payment.delay(str(order.id))
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)


@login_required
def payment_history(request):
    orders = Order.objects.filter(student=request.user, status='completed').select_related('course')
    return render(request, 'payments/payment_history.html', {'orders': orders})


@login_required
def receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, student=request.user, status='completed')
    return render(request, 'payments/receipt.html', {'order': order})
