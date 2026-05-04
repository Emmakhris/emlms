from django.contrib import admin
from .models import Thread, Reply


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'author', 'thread_type', 'is_pinned', 'is_answered', 'is_closed', 'reply_count', 'created_at']
    list_filter = ['thread_type', 'is_pinned', 'is_answered', 'is_closed']
    search_fields = ['title', 'author__email', 'course__title']
    actions = ['pin_threads', 'close_threads']

    def pin_threads(self, request, queryset):
        queryset.update(is_pinned=True)

    def close_threads(self, request, queryset):
        queryset.update(is_closed=True)


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['author', 'thread', 'is_accepted_answer', 'is_instructor_reply', 'upvotes', 'created_at']
    list_filter = ['is_accepted_answer', 'is_instructor_reply']
    search_fields = ['author__email', 'thread__title']
