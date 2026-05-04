from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin (obfuscated path)
    path('admin-emlms-secure/', admin.site.urls),

    # Core / public pages
    path('', include('apps.core.urls', namespace='core')),

    # Authentication (django-allauth)
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

    # Courses
    path('courses/', include('apps.courses.urls', namespace='courses')),

    # Lessons (accessed via course slug)
    path('courses/', include('apps.lessons.urls', namespace='lessons')),

    # Enrollments
    path('', include('apps.enrollments.urls', namespace='enrollments')),

    # Payments
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('checkout/', include('apps.payments.checkout_urls', namespace='checkout')),

    # Quizzes
    path('courses/', include('apps.quizzes.urls', namespace='quizzes')),

    # Certificates
    path('certificates/', include('apps.certificates.urls', namespace='certificates')),

    # Discussions
    path('courses/', include('apps.discussions.urls', namespace='discussions')),

    # Coupons
    path('coupons/', include('apps.coupons.urls', namespace='coupons')),

    # Dashboard
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
