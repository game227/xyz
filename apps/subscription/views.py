from django.shortcuts import render

from .services import get_active_contacts, get_active_subscription


def subscription_info_view(request):
    from apps.subscription.access import get_freemium_lesson

    subscription = None
    if request.user.is_authenticated:
        subscription = get_active_subscription(request.user)
    return render(request, 'subscription/info.html', {
        'subscription': subscription,
        'free_lesson': get_freemium_lesson(),
        'contacts': get_active_contacts(),
    })
