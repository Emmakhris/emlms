from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from .models import Thread, Reply


def _get_enrolled_or_instructor(request, course):
    if request.user.is_instructor and course.instructor == request.user:
        return True
    return Enrollment.objects.filter(student=request.user, course=course, status='active').exists()


@login_required
def thread_list(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug, status='published')
    if not _get_enrolled_or_instructor(request, course):
        messages.warning(request, 'You must be enrolled to view discussions.')
        return redirect('courses:detail', slug=course_slug)

    thread_type = request.GET.get('type', '')
    threads = Thread.objects.filter(course=course).select_related('author').order_by('-is_pinned', '-created_at')
    if thread_type:
        threads = threads.filter(thread_type=thread_type)

    return render(request, 'discussions/thread_list.html', {'course': course, 'threads': threads, 'thread_type': thread_type})


@login_required
def thread_detail(request, course_slug, thread_id):
    course = get_object_or_404(Course, slug=course_slug, status='published')
    thread = get_object_or_404(Thread, id=thread_id, course=course)

    if not _get_enrolled_or_instructor(request, course):
        return redirect('courses:detail', slug=course_slug)

    Thread.objects.filter(pk=thread.pk).update(views=thread.views + 1)

    replies = Reply.objects.filter(thread=thread, parent=None).prefetch_related('children', 'children__author').select_related('author')

    if request.method == 'POST' and not request.htmx:
        body = request.POST.get('body', '').strip()
        parent_id = request.POST.get('parent_id')
        if body:
            Reply.objects.create(
                thread=thread,
                author=request.user,
                body=body,
                parent_id=parent_id if parent_id else None,
                is_instructor_reply=request.user.is_instructor and course.instructor == request.user,
            )
        return redirect('discussions:thread_detail', course_slug=course_slug, thread_id=thread_id)

    return render(request, 'discussions/thread_detail.html', {'course': course, 'thread': thread, 'replies': replies})


@login_required
def create_thread(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug, status='published')
    if not _get_enrolled_or_instructor(request, course):
        return redirect('courses:detail', slug=course_slug)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        thread_type = request.POST.get('thread_type', 'question')
        lesson_id = request.POST.get('lesson_id') or None

        if title and body:
            thread = Thread.objects.create(
                course=course, author=request.user, title=title, body=body,
                thread_type=thread_type, lesson_id=lesson_id,
            )
            return redirect('discussions:thread_detail', course_slug=course_slug, thread_id=thread.id)
        messages.error(request, 'Title and body are required.')

    return render(request, 'discussions/create_thread.html', {'course': course})


@login_required
@require_POST
def post_reply_htmx(request, course_slug, thread_id):
    course = get_object_or_404(Course, slug=course_slug)
    thread = get_object_or_404(Thread, id=thread_id, course=course, is_closed=False)

    body = request.POST.get('body', '').strip()
    parent_id = request.POST.get('parent_id') or None

    if body:
        reply = Reply.objects.create(
            thread=thread, author=request.user, body=body,
            parent_id=parent_id,
            is_instructor_reply=request.user.is_instructor and course.instructor == request.user,
        )
        from .tasks import notify_discussion_reply
        notify_discussion_reply.delay(reply.id)
        return render(request, 'discussions/partials/reply_item.html', {'reply': reply, 'course': course})

    return render(request, 'discussions/partials/reply_error.html')


@login_required
@require_POST
def mark_accepted_answer(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    course = reply.thread.course
    if request.user != course.instructor:
        messages.error(request, 'Only the instructor can mark accepted answers.')
        return redirect('discussions:thread_detail', course_slug=course.slug, thread_id=reply.thread.id)

    reply.is_accepted_answer = True
    reply.save()
    reply.thread.is_answered = True
    reply.thread.save(update_fields=['is_answered'])
    return redirect('discussions:thread_detail', course_slug=course.slug, thread_id=reply.thread.id)
