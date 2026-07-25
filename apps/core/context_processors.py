"""Shared template context for XYZ branding."""


def site_branding(request):
    from apps.subscription.services import get_active_contacts

    return {
        'SITE_NAME': 'XYZ',
        'SITE_TAGLINE': 'Faqat matematika — universitet imtihoniga onlayn tayyorgarlik',
        'SITE_CONTACTS': get_active_contacts(),
    }
