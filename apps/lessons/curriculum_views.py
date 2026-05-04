"""
Instructor-facing curriculum management: add/edit/delete sections and lessons.
All views require is_instructor and course ownership.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from apps.courses.models import Course
from .models import Section, Lesson, VideoLesson, TextLesson, DownloadableResource


def _instructor_course(request, slug):
    """Return published-or-draft course owned by this instructor, or 404."""
    return get_object_or_404(Course, slug=slug, instructor=request.user)


@login_required
def curriculum(request, slug):
    course = _instructor_course(request, slug)
    sections = Section.objects.filter(course=course).prefetch_related('lessons').order_by('order')
    return render(request, 'lessons/curriculum.html', {
        'course': course,
        'sections': sections,
        'lesson_types': Lesson.LESSON_TYPE_CHOICES,
    })


# ── Sections ──────────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_section(request, slug):
    course = _instructor_course(request, slug)
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, 'Section title is required.')
        return redirect('courses:curriculum', slug=slug)
    order = Section.objects.filter(course=course).count()
    Section.objects.create(course=course, title=title, order=order)
    messages.success(request, f'Section "{title}" added.')
    return redirect('courses:curriculum', slug=slug)


@login_required
def edit_section(request, slug, section_id):
    course = _instructor_course(request, slug)
    section = get_object_or_404(Section, id=section_id, course=course)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        if title:
            section.title = title
            section.description = description
            section.save()
            messages.success(request, 'Section updated.')
        return redirect('courses:curriculum', slug=slug)
    return render(request, 'lessons/partials/section_edit_form.html', {'course': course, 'section': section})


@login_required
@require_POST
def delete_section(request, slug, section_id):
    course = _instructor_course(request, slug)
    section = get_object_or_404(Section, id=section_id, course=course)
    section.delete()
    _sync_course_stats(course)
    messages.success(request, 'Section deleted.')
    return redirect('courses:curriculum', slug=slug)


@login_required
@require_POST
def reorder_sections(request, slug):
    course = _instructor_course(request, slug)
    order_ids = request.POST.getlist('section_ids[]')
    for idx, sid in enumerate(order_ids):
        Section.objects.filter(id=sid, course=course).update(order=idx)
    return JsonResponse({'status': 'ok'})


# ── Lessons ───────────────────────────────────────────────────────────────────

@login_required
def add_lesson(request, slug, section_id):
    course = _instructor_course(request, slug)
    section = get_object_or_404(Section, id=section_id, course=course)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        lesson_type = request.POST.get('lesson_type', 'video')
        description = request.POST.get('description', '').strip()
        is_free_preview = bool(request.POST.get('is_free_preview'))
        duration_minutes = int(request.POST.get('duration_minutes', 0) or 0)

        if not title:
            messages.error(request, 'Lesson title is required.')
            return redirect('courses:curriculum', slug=slug)

        order = section.lessons.count()
        lesson = Lesson.objects.create(
            section=section, title=title, lesson_type=lesson_type,
            description=description, order=order,
            is_free_preview=is_free_preview, duration_minutes=duration_minutes,
        )

        # Create the content stub
        if lesson_type == 'video':
            video_url = request.POST.get('video_url', '').strip()
            VideoLesson.objects.create(lesson=lesson, video_url=video_url)
        elif lesson_type == 'text':
            content = request.POST.get('content', '').strip()
            TextLesson.objects.create(lesson=lesson, content=content)

        _sync_course_stats(course)
        messages.success(request, f'Lesson "{title}" added.')
        return redirect('courses:curriculum', slug=slug)

    return render(request, 'lessons/partials/lesson_form.html', {
        'course': course, 'section': section,
        'lesson_types': Lesson.LESSON_TYPE_CHOICES,
    })


@login_required
def edit_lesson(request, slug, lesson_id):
    course = _instructor_course(request, slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, section__course=course)

    if request.method == 'POST':
        lesson.title = request.POST.get('title', lesson.title).strip()
        lesson.description = request.POST.get('description', '').strip()
        lesson.is_free_preview = bool(request.POST.get('is_free_preview'))
        lesson.duration_minutes = int(request.POST.get('duration_minutes', 0) or 0)
        lesson.is_published = bool(request.POST.get('is_published'))
        lesson.save()

        # Update lesson-type-specific content
        if lesson.lesson_type == 'video':
            video_url = request.POST.get('video_url', '').strip()
            if video_url:
                VideoLesson.objects.update_or_create(lesson=lesson, defaults={'video_url': video_url})
        elif lesson.lesson_type == 'text':
            content = request.POST.get('content', '').strip()
            TextLesson.objects.update_or_create(lesson=lesson, defaults={'content': content})

        _sync_course_stats(course)
        messages.success(request, 'Lesson updated.')
        return redirect('courses:curriculum', slug=slug)

    return render(request, 'lessons/partials/lesson_form.html', {
        'course': course,
        'section': lesson.section,
        'lesson': lesson,
        'lesson_types': Lesson.LESSON_TYPE_CHOICES,
    })


@login_required
@require_POST
def delete_lesson(request, slug, lesson_id):
    course = _instructor_course(request, slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, section__course=course)
    lesson.delete()
    _sync_course_stats(course)
    messages.success(request, 'Lesson deleted.')
    return redirect('courses:curriculum', slug=slug)


@login_required
@require_POST
def reorder_lessons(request, slug, section_id):
    course = _instructor_course(request, slug)
    section = get_object_or_404(Section, id=section_id, course=course)
    order_ids = request.POST.getlist('lesson_ids[]')
    for idx, lid in enumerate(order_ids):
        Lesson.objects.filter(id=lid, section=section).update(order=idx)
    return JsonResponse({'status': 'ok'})


@login_required
def upload_resource(request, slug, lesson_id):
    course = _instructor_course(request, slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, section__course=course, lesson_type='resource')

    if request.method == 'GET':
        return render(request, 'lessons/partials/resource_upload_form.html', {'course': course, 'lesson': lesson})

    ALLOWED_TYPES = {
        'application/pdf', 'application/zip', 'application/x-zip-compressed',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain', 'image/jpeg', 'image/png',
    }
    MAX_SIZE = 50 * 1024 * 1024  # 50 MB

    title = request.POST.get('title', '').strip()
    f = request.FILES.get('file')
    if not title or not f:
        messages.error(request, 'Title and file are required.')
        return redirect('courses:curriculum', slug=slug)
    if f.size > MAX_SIZE:
        messages.error(request, 'File must be 50 MB or smaller.')
        return redirect('courses:curriculum', slug=slug)
    if f.content_type and f.content_type not in ALLOWED_TYPES:
        messages.error(request, 'File type not allowed. Permitted: PDF, ZIP, Word, Excel, PowerPoint, TXT, images.')
        return redirect('courses:curriculum', slug=slug)
    resource = DownloadableResource.objects.create(
        lesson=lesson,
        title=title,
        description=request.POST.get('description', '').strip(),
        file=f,
        file_size_bytes=f.size,
        file_type=f.content_type or '',
    )
    messages.success(request, f'Resource "{resource.title}" uploaded.')
    return redirect('courses:curriculum', slug=slug)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sync_course_stats(course):
    """Recalculate and save total_lessons and total_duration_minutes on the course."""
    from django.db.models import Sum
    total = Lesson.objects.filter(section__course=course, is_published=True).count()
    minutes = Lesson.objects.filter(section__course=course, is_published=True).aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    Course.objects.filter(pk=course.pk).update(total_lessons=total, total_duration_minutes=minutes)
