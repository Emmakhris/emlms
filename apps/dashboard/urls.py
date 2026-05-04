from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.student_dashboard, name='student'),
    path('instructor/', views.instructor_dashboard, name='instructor'),
]
