from django.db import models


class Thread(models.Model):
    TYPE_CHOICES = [
        ('question', 'Question'),
        ('discussion', 'Discussion'),
        ('announcement', 'Announcement'),
    ]

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='threads')
    lesson = models.ForeignKey('lessons.Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='threads')
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    thread_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='question')
    title = models.CharField(max_length=300)
    body = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_answered = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    upvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Reply(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    body = models.TextField()
    is_accepted_answer = models.BooleanField(default=False)
    is_instructor_reply = models.BooleanField(default=False)
    upvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_accepted_answer', 'created_at']

    def __str__(self):
        return f'Reply by {self.author} on "{self.thread.title}"'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.thread.reply_count += 1
            self.thread.save(update_fields=['reply_count'])


class ThreadVote(models.Model):
    VOTE_CHOICES = [(1, 'Upvote'), (-1, 'Downvote')]
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.SET_NULL, null=True, blank=True)
    reply = models.ForeignKey(Reply, on_delete=models.SET_NULL, null=True, blank=True)
    vote = models.SmallIntegerField(choices=VOTE_CHOICES)

    class Meta:
        unique_together = [['user', 'thread'], ['user', 'reply']]
