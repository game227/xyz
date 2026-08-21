from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.education.models import Lesson
from apps.subscription.access import MIN_WATCH_PERCENT_TO_COMPLETE, can_access_lesson

from .services import get_dashboard_context, mark_lesson_complete, save_watch_progress


@login_required
@require_POST
def mark_lesson_complete_view(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk, is_active=True)
    if not can_access_lesson(request.user, lesson):
        messages.warning(
            request,
            f"«{lesson.title}» pullik dars. Ochish uchun faol obuna kerak.",
        )
        return redirect('subscription:info')

    _, ok = mark_lesson_complete(request.user, lesson, require_watch=True)
    if not ok:
        messages.warning(
            request,
            f"Avval videoni kamida {MIN_WATCH_PERCENT_TO_COMPLETE}% tomosha qiling, "
            "keyin «Tugatildi» bosishingiz mumkin.",
        )
    else:
        messages.success(request, "Dars tugatilgan deb belgilandi. Endi testni boshlashingiz mumkin.")
    return redirect('education:lesson_detail', pk=lesson_pk)


@login_required
@require_POST
def save_watch_progress_view(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk, is_active=True)
    if not can_access_lesson(request.user, lesson):
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
    try:
        percent = int(request.POST.get('percent', 0))
    except (TypeError, ValueError):
        percent = 0
    progress = save_watch_progress(request.user, lesson, percent)
    return JsonResponse({
        'ok': True,
        'watch_percent': progress.watch_percent,
        'can_complete': progress.watch_percent >= MIN_WATCH_PERCENT_TO_COMPLETE,
    })


@login_required
def dashboard_view(request):
    from django.utils import timezone

    from apps.subscription.access import get_freemium_lesson
    from apps.subscription.services import get_active_subscription

    context = get_dashboard_context(request.user)
    subscription = get_active_subscription(request.user)
    context['subscription'] = subscription
    context['free_lesson'] = get_freemium_lesson()

    days_left = None
    expiring_soon = False
    if subscription and subscription.is_currently_active():
        days_left = (subscription.end_date - timezone.localdate()).days
        expiring_soon = 0 <= days_left <= 5
    context['subscription_days_left'] = days_left
    context['subscription_expiring_soon'] = expiring_soon
    return render(request, 'progress/dashboard.html', context)
