from .models import SiteSettings, Notification


def site_settings(request):
    return {'site_settings': SiteSettings.get()}


def notifications(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_notifications = Notification.objects.filter(user=request.user)[:5]
        return {
            'unread_notification_count': unread_count,
            'recent_notifications': recent_notifications,
        }
    return {
        'unread_notification_count': 0,
        'recent_notifications': [],
    }
