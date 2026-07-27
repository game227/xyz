"""Subscription services."""
import datetime

from django.utils import timezone

from apps.core.utils import get_logger

from .constants import SUBSCRIPTION_PLANS
from .models import ContactChannel, Subscription, SubscriptionRequest

logger = get_logger('subscription')


def get_subscription_plans():
    return list(SUBSCRIPTION_PLANS)


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
    """Admin action: grant `duration_days`, extending any remaining active period."""
    today = timezone.localdate()
    current = (
        Subscription.objects.filter(user=user, status=Subscription.Status.ACTIVE)
        .order_by('-end_date')
        .first()
    )
    if current:
        current.refresh_status()
        if current.is_currently_active():
            start_date = current.start_date
            end_date = current.end_date + datetime.timedelta(days=duration_days)
            current.end_date = end_date
            current.duration_days = (end_date - start_date).days
            current.activated_by = activated_by
            current.save(update_fields=[
                'end_date', 'duration_days', 'activated_by', 'updated_at',
            ])
            logger.info(
                'SUBSCRIPTION_EXTENDED: user=%s +%s days → %s by=%s',
                user.username, duration_days, end_date,
                getattr(activated_by, 'username', 'unknown'),
            )
            return current

    start_date = today
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


def create_subscription_request(*, user, full_name, phone, telegram, plan_days, note):
    req = SubscriptionRequest.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        full_name=full_name.strip(),
        phone=phone.strip(),
        telegram=(telegram or '').strip(),
        plan_days=plan_days,
        note=(note or '').strip(),
    )
    logger.info(
        'SUBSCRIPTION_REQUEST: user=%s plan=%s phone=%s',
        getattr(user, 'username', 'anon'), plan_days, phone,
    )
    return req
