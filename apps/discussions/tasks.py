from celery import shared_task


@shared_task(bind=True, max_retries=3)
def notify_discussion_reply(self, reply_id):
    """Notify the thread author (and previous participants) when a new reply is posted."""
    try:
        from .models import Reply
        from apps.core.models import Notification
        from django.conf import settings

        reply = Reply.objects.select_related(
            'thread__course', 'thread__author', 'author'
        ).get(id=reply_id)

        thread = reply.thread
        course = thread.course

        # Collect users to notify: thread author + all other reply authors, minus the poster
        notify_users = set()
        notify_users.add(thread.author_id)
        for uid in Reply.objects.filter(thread=thread).exclude(
            id=reply.id
        ).values_list('author_id', flat=True):
            notify_users.add(uid)

        notify_users.discard(reply.author_id)

        link = f'/courses/{course.slug}/discuss/{thread.id}/'
        for user_id in notify_users:
            Notification.objects.create(
                user_id=user_id,
                notif_type='discussion',
                title=f'New reply in: {thread.title}',
                message=f'{reply.author.get_full_name()} replied to a discussion you participated in.',
                link=link,
            )
    except Exception as exc:
        raise self.retry(exc=exc)
