from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('', views.my_certificates, name='list'),
    path('<uuid:pk>/', views.certificate_view, name='view'),
    path('<uuid:pk>/download/', views.certificate_download, name='download'),
    path('verify/<str:code>/', views.certificate_verify, name='verify'),
]
