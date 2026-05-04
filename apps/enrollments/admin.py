from django.contrib import admin
from .models import Enrollment, CourseProgress


class CourseProgressInline(admin.StackedInline):
    model = CourseProgress
    can_delete = False
    extra = 0
    readonly_fields = ['lessons_completed', 'total_lessons', 'percentage', 'last_accessed_at']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'amount_paid', 'enrolled_at', 'completed_at']
    list_filter = ['status']
    search_fields = ['student__email', 'course__title']
    date_hierarchy = 'enrolled_at'
    inlines = [CourseProgressInline]
