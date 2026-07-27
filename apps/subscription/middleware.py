"""Global subscription + freemium gate.

Authenticated users without an active subscription may only:
- browse curriculum lists
- open the platform's first free lesson + its related test
- use dashboard / exam history (so progress and free results remain visible)

Everything else redirects to the subscription info page.
"""
from django.contrib import messages
from django.shortcuts import redirect

from .access import is_request_allowed_without_subscription
from .services import has_active_subscription

PROTECTED_NAMESPACES = {'education', 'exam', 'progress'}


class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None

        # Teachers/admins manage content and preview curriculum without subscription.
        if getattr(request.user, 'can_manage_content', False):
            return None

        resolver_match = request.resolver_match
        namespace = resolver_match.namespace if resolver_match else None
        if namespace not in PROTECTED_NAMESPACES:
            return None

        if has_active_subscription(request.user):
            return None

        if is_request_allowed_without_subscription(request):
            return None

        messages.warning(
            request,
            "Bu dars yoki test pullik. Katalogni ko‘rishingiz mumkin, lekin ochish uchun "
            "faol obuna kerak. Obuna sahifasidan tarif tanlab so‘rov yuboring yoki "
            "administrator bilan bog‘laning.",
        )
        return redirect('subscription:info')
