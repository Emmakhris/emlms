from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    path('<slug:course_slug>/learn/', views.course_learn, name='learn'),
    path('<slug:course_slug>/learn/<uuid:lesson_id>/', views.course_learn, name='learn_lesson'),
    path('lessons/<uuid:lesson_id>/complete/', views.mark_lesson_complete, name='mark_complete'),
    path('lessons/<uuid:lesson_id>/progress/', views.save_video_progress, name='save_progress'),
]
