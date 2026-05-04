from django.urls import path
from . import views

app_name = 'enrollments'

urlpatterns = [
    path('enroll/<slug:slug>/', views.enroll_free, name='enroll_free'),
    path('my-courses/', views.my_courses, name='my_courses'),
]
