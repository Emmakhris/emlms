from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404


class InstructorRequiredMixin(LoginRequiredMixin):
    """Allow access only to users with is_instructor=True."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_instructor:
            messages.error(request, 'You need instructor privileges to access this page.')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)


class EnrollmentRequiredMixin(LoginRequiredMixin):
    """Allow access to lesson/content views only for enrolled students."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        from apps.courses.models import Course
        from apps.enrollments.models import Enrollment
        self.course = get_object_or_404(Course, slug=kwargs.get('course_slug'))
        # Instructors always have access to their own course content
        if request.user.is_instructor and self.course.instructor == request.user:
            return super().dispatch(request, *args, **kwargs)
        # Free preview lessons skip enrollment check (handled in view)
        is_enrolled = Enrollment.objects.filter(
            student=request.user,
            course=self.course,
            status='active'
        ).exists()
        if not is_enrolled:
            messages.warning(request, 'Please enroll in this course to access its content.')
            return redirect('courses:detail', slug=self.course.slug)
        return super().dispatch(request, *args, **kwargs)
