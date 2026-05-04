from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, InstructorProfile


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    extra = 0


class InstructorProfileInline(admin.StackedInline):
    model = InstructorProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_instructor', 'is_student', 'is_active', 'created_at']
    list_filter = ['is_instructor', 'is_student', 'is_active', 'is_staff', 'country']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    inlines = [StudentProfileInline, InstructorProfileInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'avatar', 'bio', 'phone_number', 'country', 'date_of_birth')}),
        ('Roles', {'fields': ('is_student', 'is_instructor', 'is_email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_student', 'is_instructor'),
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'streak_days', 'total_learning_hours', 'last_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified', 'total_students', 'total_courses', 'total_revenue', 'rating']
    list_filter = ['is_verified']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
