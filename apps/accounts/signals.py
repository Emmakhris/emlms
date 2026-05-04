from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, StudentProfile, InstructorProfile


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    if created and instance.is_student:
        StudentProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_instructor_profile(sender, instance, **kwargs):
    if instance.is_instructor:
        InstructorProfile.objects.get_or_create(user=instance)
