from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import SubscriptionRequestForm
from .services import (
    create_subscription_request,
    get_active_contacts,
    get_active_subscription,
    get_subscription_plans,
)


def subscription_info_view(request):
    from apps.subscription.access import get_freemium_lesson

    subscription = None
    if request.user.is_authenticated:
        subscription = get_active_subscription(request.user)

    form = SubscriptionRequestForm(
        request.POST or None,
        user=request.user if request.user.is_authenticated else None,
    )

    if request.method == 'POST':
        if form.is_valid():
            create_subscription_request(
                user=request.user,
                full_name=form.cleaned_data['full_name'],
                phone=form.cleaned_data['phone'],
                telegram=form.cleaned_data['telegram'],
                plan_days=form.cleaned_data['plan_days'],
                note=form.cleaned_data['note'],
            )
            messages.success(
                request,
                'So‘rovingiz qabul qilindi. Administrator tez orada bog‘lanadi.',
            )
            return redirect('subscription:info')
        messages.error(request, 'So‘rovni tekshirib, qayta yuboring.')

    return render(request, 'subscription/info.html', {
        'subscription': subscription,
        'free_lesson': get_freemium_lesson(),
        'contacts': get_active_contacts(),
        'plans': get_subscription_plans(),
        'form': form,
    })
