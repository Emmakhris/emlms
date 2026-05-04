import uuid
from django.db import models


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField('enrollments.Enrollment', on_delete=models.CASCADE, related_name='certificate')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='certificates')
    verification_code = models.CharField(max_length=20, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    # Snapshot fields
    student_name = models.CharField(max_length=200)
    course_title = models.CharField(max_length=200)
    instructor_name = models.CharField(max_length=200)
    completion_date = models.DateField()
    course_duration_hours = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    is_valid = models.BooleanField(default=True)

    def __str__(self):
        return f'Certificate — {self.student_name} — {self.course_title}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('certificates:view', kwargs={'pk': str(self.id)})
