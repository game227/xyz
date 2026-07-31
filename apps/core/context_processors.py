"""Shared template context for XYZ branding."""


def site_branding(request):
    from apps.subscription.services import get_active_contacts
    from apps.core.models import SiteSettings

    settings_obj = SiteSettings.load()
    return {
        'SITE_NAME': settings_obj.site_name or 'XYZ',
        'SITE_TAGLINE': settings_obj.tagline or (
            'Faqat matematika — universitet imtihoniga onlayn tayyorgarlik'
        ),
        'SITE_LOGO': settings_obj.logo if settings_obj.logo else None,
        'SITE_FAVICON': settings_obj.favicon if settings_obj.favicon else None,
        'SITE_CONTACTS': get_active_contacts(),
        'SITE_SETTINGS': settings_obj,
    }
