import uuid
from django.db import models
from django.utils import timezone


class Section(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Lesson(models.Model):
    LESSON_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Text / Article'),
        ('quiz', 'Quiz'),
        ('resource', 'Downloadable Resource'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES)
    order = models.PositiveSmallIntegerField(default=0)
    duration_minutes = models.PositiveSmallIntegerField(default=0)
    is_free_preview = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['section__order', 'order']

    def __str__(self):
        return f'{self.section.course.title} / {self.section.title} / {self.title}'

    @property
    def course(self):
        return self.section.course


class VideoLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='video')
    video_url = models.URLField()
    video_public_id = models.CharField(max_length=200, blank=True)
    thumbnail_url = models.URLField(blank=True)
    transcript = models.TextField(blank=True)
    captions_url = models.URLField(blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    resolution = models.CharField(max_length=20, blank=True)

    def get_stream_url(self):
        """Return playable URL — direct video_url for now; swap for signed Cloudinary URL in production."""
        return self.video_url

    def __str__(self):
        return f'Video — {self.lesson.title}'


class TextLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='text')
    content = models.TextField()
    reading_time_minutes = models.PositiveSmallIntegerField(default=5)

    @property
    def rendered_html(self):
        import markdown
        import bleach
        allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
            'p', 'h1', 'h2', 'h3', 'h4', 'pre', 'code', 'blockquote', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        ]
        allowed_attrs = {**bleach.sanitizer.ALLOWED_ATTRIBUTES, 'img': ['src', 'alt'], 'a': ['href', 'title']}
        html = markdown.markdown(self.content, extensions=['fenced_code', 'tables'])
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=False)

    def __str__(self):
        return f'Text — {self.lesson.title}'


class DownloadableResource(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    file = models.FileField(upload_to='resources/%Y/%m/')
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    file_type = models.CharField(max_length=20, blank=True)
    download_count = models.PositiveIntegerField(default=0)

    def get_download_url(self):
        return self.file.url if self.file else ''

    def __str__(self):
        return f'{self.title} ({self.lesson.title})'

    def get_human_size(self):
        import humanize
        return humanize.naturalsize(self.file_size_bytes)


class LessonProgress(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    watch_time_seconds = models.PositiveIntegerField(default=0)
    last_position_seconds = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'lesson']

    def mark_complete(self):
        if self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()

    def __str__(self):
        return f'{self.student} — {self.lesson.title} ({self.status})'
