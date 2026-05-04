from django.contrib import admin
from .models import Section, Lesson, VideoLesson, TextLesson, DownloadableResource, LessonProgress


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ['title', 'lesson_type', 'order', 'duration_minutes', 'is_free_preview', 'is_published']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'lesson_type', 'order', 'duration_minutes', 'is_free_preview', 'is_published']
    list_filter = ['lesson_type', 'is_free_preview', 'is_published']
    search_fields = ['title', 'section__course__title']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'status', 'watch_time_seconds', 'completed_at']
    list_filter = ['status']
    search_fields = ['student__email', 'lesson__title']
