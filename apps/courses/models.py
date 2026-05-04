import uuid
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CourseTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    PRICING_CHOICES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='courses_taught')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    tags = models.ManyToManyField(CourseTag, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/', null=True, blank=True)
    preview_video_url = models.URLField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='all')
    language = models.CharField(max_length=50, default='English')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    pricing_type = models.CharField(max_length=10, choices=PRICING_CHOICES, default='free')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='GHS')
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    total_enrolled = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    total_duration_minutes = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    certificate_enabled = models.BooleanField(default=True)
    discussion_enabled = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'pricing_type']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        if self.pricing_type == 'free':
            return 0
        if self.discounted_price is not None:
            return self.discounted_price
        return self.price

    @property
    def has_discount(self):
        return self.discounted_price is not None and self.discounted_price < self.price

    @property
    def discount_percentage(self):
        if self.has_discount:
            return int((1 - self.discounted_price / self.price) * 100)
        return 0

    def get_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return '/static/images/course-placeholder.svg'


class CourseRequirement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='requirements')
    text = models.CharField(max_length=300)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.text[:50]}'


class WhatYouLearn(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='outcomes')
    text = models.CharField(max_length=300)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.text[:50]}'


class CourseReview(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reviews_given')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['course', 'student']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} → {self.course.title} ({self.rating}★)'
