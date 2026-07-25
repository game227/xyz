"""Subscription services."""
import datetime

from django.utils import timezone

from apps.core.utils import get_logger

from .models import ContactChannel, Subscription

logger = get_logger('subscription')


def get_active_contacts():
    return list(ContactChannel.objects.filter(is_active=True).order_by('order', 'id'))


def get_active_subscription(user):
    """Return the user's most recent subscription (status refreshed),
    or None if they've never had one. The dashboard/middleware treat a
    non-active result the same way regardless of *why* it's inactive."""
    if not user.is_authenticated:
        return None
    subscription = Subscription.objects.filter(user=user).order_by('-end_date').first()
    if subscription:
        subscription.refresh_status()
    return subscription


def has_active_subscription(user):
    subscription = get_active_subscription(user)
    return bool(subscription and subscription.is_currently_active())


def activate_subscription(user, duration_days, activated_by):
    """Admin action: grant `duration_days` starting today."""
    start_date = timezone.localdate()
    end_date = start_date + datetime.timedelta(days=duration_days)
    subscription = Subscription.objects.create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        duration_days=duration_days,
        status=Subscription.Status.ACTIVE,
        activated_by=activated_by,
    )
    logger.info(
        'SUBSCRIPTION_ACTIVATED: user=%s days=%s by=%s',
        user.username, duration_days, getattr(activated_by, 'username', 'unknown'),
    )
    return subscription
