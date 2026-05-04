from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='notifications_read_all'),
]
