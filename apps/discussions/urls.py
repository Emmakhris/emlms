from django.urls import path
from . import views

app_name = 'discussions'

urlpatterns = [
    path('<slug:course_slug>/discuss/', views.thread_list, name='thread_list'),
    path('<slug:course_slug>/discuss/new/', views.create_thread, name='create_thread'),
    path('<slug:course_slug>/discuss/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('<slug:course_slug>/discuss/<int:thread_id>/reply/', views.post_reply_htmx, name='post_reply'),
    path('replies/<int:reply_id>/accept/', views.mark_accepted_answer, name='mark_accepted'),
]
