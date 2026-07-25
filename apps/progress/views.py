from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.education.models import Lesson

from .services import get_dashboard_context, mark_lesson_complete


@login_required
def mark_lesson_complete_view(request, lesson_pk):
    if request.method != 'POST':
        return redirect('education:lesson_detail', pk=lesson_pk)

    from apps.subscription.access import can_access_lesson

    lesson = get_object_or_404(Lesson, pk=lesson_pk, is_active=True)
    if not can_access_lesson(request.user, lesson):
        messages.warning(request, "Bu dars uchun faol obuna kerak.")
        return redirect('subscription:info')

    mark_lesson_complete(request.user, lesson)
    messages.success(request, "Dars tugatilgan deb belgilandi.")
    return redirect('education:lesson_detail', pk=lesson_pk)


@login_required
def dashboard_view(request):
    from apps.subscription.access import get_freemium_lesson
    from apps.subscription.services import get_active_subscription

    context = get_dashboard_context(request.user)
    context['subscription'] = get_active_subscription(request.user)
    context['free_lesson'] = get_freemium_lesson()
    return render(request, 'progress/dashboard.html', context)
