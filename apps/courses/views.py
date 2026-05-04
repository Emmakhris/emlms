from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django_htmx.http import HttpResponseClientRefresh

from apps.core.mixins import InstructorRequiredMixin
from .models import Course, Category, CourseReview
from .forms import CourseForm, CourseReviewForm


class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        qs = Course.objects.filter(status='published').select_related('instructor', 'category')

        category = self.request.GET.get('category')
        level = self.request.GET.get('level')
        pricing = self.request.GET.get('pricing')
        sort = self.request.GET.get('sort', '-published_at')
        q = self.request.GET.get('q', '')

        if category:
            qs = qs.filter(category__slug=category)
        if level:
            qs = qs.filter(level=level)
        if pricing:
            qs = qs.filter(pricing_type=pricing)
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(instructor__first_name__icontains=q))

        valid_sorts = ['-published_at', '-total_enrolled', '-average_rating', 'price', '-price']
        if sort in valid_sorts:
            qs = qs.order_by(sort)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(is_active=True, parent=None)
        ctx['course_levels'] = [
            ('', 'All Levels'),
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ]
        ctx['current_filters'] = {
            'category': self.request.GET.get('category', ''),
            'level': self.request.GET.get('level', ''),
            'pricing': self.request.GET.get('pricing', ''),
            'sort': self.request.GET.get('sort', '-published_at'),
            'q': self.request.GET.get('q', ''),
        }
        return ctx


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Course.objects.filter(status='published').select_related('instructor', 'category').prefetch_related(
            'requirements', 'outcomes', 'tags', 'sections__lessons'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user

        ctx['is_enrolled'] = False
        ctx['user_review'] = None

        if user.is_authenticated:
            from apps.enrollments.models import Enrollment
            ctx['is_enrolled'] = Enrollment.objects.filter(
                student=user, course=course, status='active'
            ).exists()
            ctx['user_review'] = CourseReview.objects.filter(course=course, student=user).first()

        ctx['reviews'] = course.reviews.filter(is_approved=True).select_related('student')[:10]
        ctx['review_form'] = CourseReviewForm()
        return ctx


class CourseCreateView(InstructorRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        messages.success(self.request, 'Course created successfully. Now add your curriculum.')
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse
        return reverse('courses:curriculum', kwargs={'slug': self.object.slug})


class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Course updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse
        return reverse('courses:detail', kwargs={'slug': self.object.slug})


@login_required
def submit_review(request, slug):
    course = get_object_or_404(Course, slug=slug, status='published')
    from apps.enrollments.models import Enrollment
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You must be enrolled to review this course.')
        return redirect('courses:detail', slug=slug)

    existing = CourseReview.objects.filter(course=course, student=request.user).first()
    form = CourseReviewForm(request.POST, instance=existing)

    if form.is_valid():
        review = form.save(commit=False)
        review.course = course
        review.student = request.user
        review.save()
        _update_course_rating(course)
        messages.success(request, 'Review submitted.')

    return redirect('courses:detail', slug=slug)


def _update_course_rating(course):
    from django.db.models import Avg, Count
    agg = CourseReview.objects.filter(course=course, is_approved=True).aggregate(
        avg=Avg('rating'), count=Count('id')
    )
    Course.objects.filter(pk=course.pk).update(
        average_rating=round(agg['avg'] or 0, 2),
        total_reviews=agg['count'] or 0,
    )


@login_required
def toggle_publish(request, slug):
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    if course.status == 'published':
        course.status = 'draft'
        messages.info(request, 'Course unpublished.')
    else:
        course.status = 'published'
        messages.success(request, 'Course is now published!')
    course.save()
    return redirect('courses:detail', slug=slug)
