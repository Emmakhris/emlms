from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('<slug:course_slug>/quiz/<int:quiz_id>/', views.take_quiz, name='take'),
    path('<slug:course_slug>/quiz/<int:quiz_id>/result/', views.quiz_result, name='result'),
    path('<slug:course_slug>/quiz/<int:quiz_id>/result/<int:attempt_id>/', views.quiz_result, name='result_attempt'),
]
