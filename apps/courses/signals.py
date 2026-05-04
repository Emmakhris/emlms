from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count


@receiver([post_save, post_delete], sender='courses.CourseReview')
def update_course_rating(sender, instance, **kwargs):
    course = instance.course
    agg = course.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'), count=Count('id'))
    course.average_rating = agg['avg'] or 0
    course.total_reviews = agg['count'] or 0
    course.save(update_fields=['average_rating', 'total_reviews'])
