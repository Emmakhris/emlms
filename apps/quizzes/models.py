from django.db import models
from django.utils import timezone


class Quiz(models.Model):
    lesson = models.OneToOneField('lessons.Lesson', on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    pass_percentage = models.PositiveSmallIntegerField(default=70)
    time_limit_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    shuffle_questions = models.BooleanField(default=False)
    show_answers_after = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Quiz: {self.title}'


class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice (Single)'),
        ('msq', 'Multiple Choice (Multiple)'),
        ('true_false', 'True / False'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    explanation = models.TextField(blank=True)
    points = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(upload_to='quiz/questions/', null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.quiz.title} — Q{self.order}: {self.text[:60]}'


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{"✓" if self.is_correct else "✗"} {self.text[:60]}'


class QuizAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('timed_out', 'Timed Out'),
    ]

    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_score = models.PositiveSmallIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.PositiveIntegerField(default=0)
    attempt_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.student} — {self.quiz.title} attempt #{self.attempt_number}'


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choices = models.ManyToManyField(Choice, blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'{self.attempt} — {self.question}'
