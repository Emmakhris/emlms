from django.contrib import admin
from .models import Category, Course, CourseTag, CourseRequirement, WhatYouLearn, CourseReview


class CourseRequirementInline(admin.TabularInline):
    model = CourseRequirement
    extra = 2


class WhatYouLearnInline(admin.TabularInline):
    model = WhatYouLearn
    extra = 3


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'is_active']
    list_filter = ['is_active', 'parent']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(CourseTag)
class CourseTagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'category', 'status', 'pricing_type', 'price', 'total_enrolled', 'average_rating', 'is_featured']
    list_filter = ['status', 'pricing_type', 'level', 'category', 'is_featured', 'certificate_enabled']
    search_fields = ['title', 'instructor__email', 'instructor__first_name']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    inlines = [CourseRequirementInline, WhatYouLearnInline]
    actions = ['publish_courses', 'archive_courses', 'feature_courses']

    def publish_courses(self, request, queryset):
        queryset.update(status='published')
    publish_courses.short_description = 'Publish selected courses'

    def archive_courses(self, request, queryset):
        queryset.update(status='archived')
    archive_courses.short_description = 'Archive selected courses'

    def feature_courses(self, request, queryset):
        queryset.update(is_featured=True)
    feature_courses.short_description = 'Mark as featured'


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['course', 'student', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved']
    search_fields = ['course__title', 'student__email']
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = 'Approve selected reviews'

    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    reject_reviews.short_description = 'Reject selected reviews'
