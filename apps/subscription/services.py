"""Subscription services."""
import datetime

from django.utils import timezone

from apps.core.utils import get_logger

from .constants import SUBSCRIPTION_PLANS
from .models import ContactChannel, Subscription, SubscriptionPricing, SubscriptionRequest

logger = get_logger('subscription')


def ensure_default_pricing():
    """Birinchi ishga tushirishda default tariflarni yaratadi."""
    if SubscriptionPricing.objects.exists():
        return
    for i, plan in enumerate(SUBSCRIPTION_PLANS):
        price_digits = ''.join(ch for ch in plan['price_label'] if ch.isdigit())
        SubscriptionPricing.objects.create(
            title=plan['title'],
            price_uzs=int(price_digits) if price_digits else 0,
            duration_days=plan['days'],
            description=plan['blurb'],
            is_popular=plan.get('popular', False),
            order=i,
            is_active=True,
        )


def get_subscription_plans():
    ensure_default_pricing()
    rows = list(
        SubscriptionPricing.objects.filter(is_active=True).order_by('order', 'duration_days', 'id')
    )
    return [
        {
            'days': row.duration_days,
            'title': row.title,
            'price_label': row.price_label,
            'blurb': row.description or f'{row.duration_days} kunlik to‘liq kirish',
            'popular': row.is_popular,
            'pk': row.pk,
        }
        for row in rows
    ]


def get_plan_day_choices():
    plans = get_subscription_plans()
    if plans:
        return [(p['days'], p['title']) for p in plans]
    return [(30, '1 oy')]


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
            current.expiry_reminder_sent_at = None
            current.expiry_final_reminder_sent_at = None
            current.save(update_fields=[
                'end_date', 'duration_days', 'activated_by',
                'expiry_reminder_sent_at', 'expiry_final_reminder_sent_at', 'updated_at',
            ])
            logger.info(
                'SUBSCRIPTION_EXTENDED: user=%s +%s days → %s by=%s',
                user.username, duration_days, end_date,
                getattr(activated_by, 'username', 'unknown'),
            )
            _notify_subscription_activated(current)
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
    _notify_subscription_activated(subscription)
    return subscription


def _notify_subscription_activated(subscription):
    """Obuna faollashganda foydalanuvchiga bildirishnoma yuboradi (boshlanish/tugash sanasi bilan)."""
    from django.urls import reverse

    from apps.core.services import notify_user

    notify_user(
        subscription.user,
        ntype='SUB_ACTIVATED',
        title='Obuna faollashtirildi',
        message=(
            f'Obunangiz {subscription.start_date:%d.%m.%Y} sanada faollashtirildi va '
            f'{subscription.end_date:%d.%m.%Y} sanagacha amal qiladi.'
        ),
        url=reverse('subscription:info'),
    )


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
