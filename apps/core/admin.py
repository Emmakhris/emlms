from django.contrib import admin
from .models import SiteSettings, Notification, ActivityLog


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'contact_email', 'maintenance_mode', 'allow_registration']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notif_type', 'title', 'is_read', 'created_at']
    list_filter = ['notif_type', 'is_read']
    search_fields = ['user__email', 'title']
    date_hierarchy = 'created_at'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'description', 'created_at']
    list_filter = ['action']
    search_fields = ['user__email', 'description']
    date_hierarchy = 'created_at'
