from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    applicable_courses = models.ManyToManyField('courses.Course', blank=True)
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveSmallIntegerField(default=1)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self, user=None, course=None, amount=0):
        now = timezone.now()
        if not self.is_active:
            return False, 'This coupon is inactive.'
        if now < self.valid_from:
            return False, 'This coupon is not yet valid.'
        if self.valid_until and now > self.valid_until:
            return False, 'This coupon has expired.'
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False, 'This coupon has reached its usage limit.'
        if amount < self.minimum_purchase:
            return False, f'Minimum purchase of {self.minimum_purchase} required.'
        if course and self.applicable_courses.exists():
            if not self.applicable_courses.filter(pk=course.pk).exists():
                return False, 'This coupon is not valid for this course.'
        if user and self.per_user_limit:
            user_uses = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_uses >= self.per_user_limit:
                return False, 'You have already used this coupon.'
        return True, 'Valid'

    def calculate_discount(self, amount):
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = min(self.discount_value, amount)
        return discount


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    order = models.ForeignKey('payments.Order', on_delete=models.CASCADE)
    discount_given = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} used {self.coupon.code}'
