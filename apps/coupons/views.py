from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Coupon


@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get('code', '').strip().upper()
    course_id = request.POST.get('course_id', '')
    amount = Decimal(str(request.POST.get('amount', 0)))

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        if request.htmx:
            return render(request, 'coupons/partials/coupon_result.html', {
                'error': 'Invalid coupon code.',
                'code': code,
            })
        return JsonResponse({'error': 'Invalid coupon code.'}, status=400)

    from apps.courses.models import Course
    course = Course.objects.filter(id=course_id).first()
    is_valid, message = coupon.is_valid(user=request.user, course=course, amount=amount)

    if not is_valid:
        if request.htmx:
            return render(request, 'coupons/partials/coupon_result.html', {
                'error': message, 'code': code,
            })
        return JsonResponse({'error': message}, status=400)

    discount = coupon.calculate_discount(amount)
    final_amount = max(0, amount - discount)

    if request.htmx:
        return render(request, 'coupons/partials/coupon_result.html', {
            'coupon': coupon,
            'discount': discount,
            'final_amount': final_amount,
            'original_amount': amount,
        })

    return JsonResponse({
        'valid': True,
        'discount': float(discount),
        'final_amount': float(final_amount),
        'coupon_code': coupon.code,
    })
