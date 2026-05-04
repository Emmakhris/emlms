from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [
    path('<slug:slug>/', views.checkout, name='checkout'),
    path('<slug:slug>/pay/', views.initialize_payment, name='initialize'),
]
