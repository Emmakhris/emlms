from django.contrib import admin
from .models import Order, PaymentTransaction, RefundRequest


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ['paystack_reference', 'amount_kobo', 'currency', 'status', 'channel', 'paid_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['reference', 'student', 'course', 'final_amount', 'currency', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'currency', 'payment_method']
    search_fields = ['reference', 'student__email', 'course__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['reference', 'ip_address', 'paystack_transaction_id']
    inlines = [PaymentTransactionInline]


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ['order', 'requested_by', 'status', 'created_at', 'resolved_at']
    list_filter = ['status']
    search_fields = ['order__reference', 'requested_by__email']
    actions = ['approve_refunds', 'reject_refunds']

    def approve_refunds(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='approved', resolved_at=timezone.now())
    approve_refunds.short_description = 'Approve selected refund requests'

    def reject_refunds(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='rejected', resolved_at=timezone.now())
    reject_refunds.short_description = 'Reject selected refund requests'
