from django.db import models


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='EMLMS')
    tagline = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='site/', null=True, blank=True)
    favicon = models.ImageField(upload_to='site/', null=True, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    maintenance_mode = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    about_text = models.TextField(blank=True)
    hero_title = models.CharField(max_length=200, default='Learn Without Limits')
    hero_subtitle = models.CharField(max_length=400, blank=True)
    total_students_display = models.PositiveIntegerField(default=0)
    total_courses_display = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ('enrollment', 'Enrollment'),
        ('lesson_complete', 'Lesson Complete'),
        ('quiz_result', 'Quiz Result'),
        ('certificate', 'Certificate'),
        ('payment', 'Payment'),
        ('discussion', 'Discussion Reply'),
        ('announcement', 'Announcement'),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.notif_type} → {self.user}'


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('enrolled', 'Enrolled in course'),
        ('lesson_completed', 'Completed lesson'),
        ('quiz_passed', 'Passed quiz'),
        ('quiz_failed', 'Failed quiz'),
        ('certificate_earned', 'Earned certificate'),
        ('payment_made', 'Made payment'),
        ('review_posted', 'Posted review'),
        ('discussion_posted', 'Posted in discussion'),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.action}'
