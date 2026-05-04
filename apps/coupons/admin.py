from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'usage_count', 'usage_limit', 'is_active', 'valid_from', 'valid_until']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code', 'description']
    filter_horizontal = ['applicable_courses']


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'discount_given', 'used_at']
    list_filter = ['coupon']
    search_fields = ['user__email', 'coupon__code']
