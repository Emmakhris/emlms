from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('verify/', views.verify_payment, name='verify'),
    path('webhook/', views.paystack_webhook, name='webhook'),
    path('history/', views.payment_history, name='history'),
    path('receipt/<uuid:order_id>/', views.receipt, name='receipt'),
]
