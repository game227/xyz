"""Shared template context for XYZ branding."""


def site_branding(request):
    from apps.subscription.services import get_active_contacts
    from apps.core.models import SiteSettings
    from apps.live.models import LiveSession

    settings_obj = SiteSettings.load()

    notifications_ctx = {'NOTIFICATIONS_UNREAD': 0, 'NOTIFICATIONS_RECENT': []}
    if request.user.is_authenticated:
        from apps.core.models import Notification
        own = Notification.objects.filter(user=request.user)
        notifications_ctx = {
            'NOTIFICATIONS_UNREAD': own.filter(is_read=False).count(),
            'NOTIFICATIONS_RECENT': list(own[:8]),
        }

    return {
        **notifications_ctx,
        'SITE_NAME': settings_obj.site_name or 'XYZ',
        'SITE_TAGLINE': settings_obj.tagline or (
            'Faqat matematika — universitet imtihoniga onlayn tayyorgarlik'
        ),
        'SITE_LOGO': settings_obj.logo if settings_obj.logo else None,
        'SITE_FAVICON': settings_obj.favicon if settings_obj.favicon else None,
        'SITE_CONTACTS': get_active_contacts(),
        'SITE_SETTINGS': settings_obj,
        'IS_LIVE_NOW': LiveSession.objects.filter(status=LiveSession.Status.LIVE).exists(),
    }
