from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.courses.models import Course, Category
from .models import Notification, SiteSettings


def home(request):
    featured_courses = Course.objects.filter(status='published', is_featured=True).select_related('instructor', 'category')[:8]
    latest_courses = Course.objects.filter(status='published').select_related('instructor', 'category').order_by('-published_at')[:8]
    categories = Category.objects.filter(is_active=True, parent=None).order_by('order')[:8]
    site_settings = SiteSettings.get()

    context = {
        'featured_courses': featured_courses,
        'latest_courses': latest_courses,
        'categories': categories,
        'site_settings': site_settings,
    }
    return render(request, 'core/home.html', context)


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    if request.method == 'POST':
        # Basic contact form handler — extend with email sending
        from django.contrib import messages
        messages.success(request, 'Your message has been sent. We will get back to you shortly.')
        return redirect('core:contact')
    return render(request, 'core/contact.html')


def faq(request):
    return render(request, 'core/faq.html')


@login_required
@require_POST
def mark_notification_read(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    if request.htmx:
        return render(request, 'core/partials/notification_item.html', {'notification': Notification.objects.get(pk=pk)})
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', '/'))
