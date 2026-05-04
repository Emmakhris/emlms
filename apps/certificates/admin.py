from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_title', 'verification_code', 'is_valid', 'issued_at']
    list_filter = ['is_valid']
    search_fields = ['student_name', 'course_title', 'verification_code']
    readonly_fields = ['id', 'verification_code', 'issued_at', 'student_name', 'course_title', 'instructor_name']
    date_hierarchy = 'issued_at'
