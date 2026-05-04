"""
python manage.py setup_initial_data

Creates:
- SiteSettings singleton (if missing)
- Initial course categories
- Celery Beat periodic task schedules
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed initial SiteSettings, categories, and Celery Beat schedules'

    def handle(self, *args, **options):
        self._setup_site_settings()
        self._setup_categories()
        self._setup_beat_schedules()
        self.stdout.write(self.style.SUCCESS('Initial data setup complete.'))

    def _setup_site_settings(self):
        from apps.core.models import SiteSettings
        obj, created = SiteSettings.objects.get_or_create(pk=1)
        if created:
            self.stdout.write('  Created SiteSettings.')
        else:
            self.stdout.write('  SiteSettings already exists.')

    def _setup_categories(self):
        from apps.courses.models import Category
        categories = [
            ('Web Development', 'web-development', 1),
            ('Data Science', 'data-science', 2),
            ('Mobile Development', 'mobile-development', 3),
            ('Design & UX', 'design-ux', 4),
            ('Business', 'business', 5),
            ('Marketing', 'marketing', 6),
            ('Finance', 'finance', 7),
            ('Personal Development', 'personal-development', 8),
        ]
        created_count = 0
        for name, slug, order in categories:
            _, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'order': order, 'is_active': True},
            )
            if created:
                created_count += 1
        self.stdout.write(f'  Created {created_count} categories.')

    def _setup_beat_schedules(self):
        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
        except ImportError:
            self.stdout.write('  django_celery_beat not available — skipping beat schedules.')
            return

        # Every hour
        hourly, _ = IntervalSchedule.objects.get_or_create(
            every=1, period=IntervalSchedule.HOURS
        )
        # Daily at 2am
        nightly, _ = CrontabSchedule.objects.get_or_create(
            minute='0', hour='2', day_of_week='*',
            day_of_month='*', month_of_year='*',
        )
        # Sundays at 8am
        weekly, _ = CrontabSchedule.objects.get_or_create(
            minute='0', hour='8', day_of_week='0',
            day_of_month='*', month_of_year='*',
        )

        tasks = [
            ('check_course_completions', 'apps.core.tasks.check_course_completions', hourly, None),
            ('update_course_statistics', 'apps.core.tasks.update_course_statistics', None, nightly),
            ('send_weekly_progress_digest', 'apps.core.tasks.send_weekly_progress_digest', None, weekly),
        ]

        created_count = 0
        for name, task_path, interval, crontab in tasks:
            defaults = {'task': task_path, 'enabled': True}
            if interval:
                defaults['interval'] = interval
            if crontab:
                defaults['crontab'] = crontab

            _, created = PeriodicTask.objects.get_or_create(name=name, defaults=defaults)
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} periodic tasks.')
