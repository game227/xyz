from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import CustomUser

from .models import LiveChatMessage, LiveSession


@login_required
def live_watch(request):
    """Jonli dars — faqat login qilgan foydalanuvchilar."""
    session = (
        LiveSession.objects.filter(status=LiveSession.Status.LIVE)
        .select_related('host')
        .order_by('-started_at')
        .first()
    )
    if not session:
        session = (
            LiveSession.objects.select_related('host')
            .order_by('-created_at')
            .first()
        )
    chat = []
    if session:
        chat = list(
            session.messages.select_related('user').order_by('-created_at')[:80]
        )
        chat.reverse()
    return render(request, 'live/watch.html', {
        'session': session,
        'chat_messages': chat,
        'is_host_view': False,
    })


@login_required
def live_host(request):
    """O‘qituvchi/admin efirni boshqaradi."""
    user = request.user
    if not (user.can_manage_content or user.is_staff):
        messages.error(request, 'Jonli efirni faqat o‘qituvchi yoki admin boshqaradi.')
        return redirect('live:watch')

    session = (
        LiveSession.objects.filter(host=user, status=LiveSession.Status.LIVE)
        .order_by('-started_at')
        .first()
    )
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'start':
            title = (request.POST.get('title') or '').strip() or 'Jonli matematika darsi'
            if session:
                messages.info(request, 'Sizda allaqachon jonli efir bor.')
            else:
                LiveSession.objects.filter(
                    host=user, status=LiveSession.Status.LIVE
                ).update(status=LiveSession.Status.ENDED)
                session = LiveSession.objects.create(
                    title=title,
                    host=user,
                    status=LiveSession.Status.LIVE,
                )
                session.mark_live()
                messages.success(request, 'Jonli efir boshlandi.')
            return redirect('live:host')
        if action == 'end' and session:
            session.mark_ended()
            messages.success(request, 'Efir yakunlandi.')
            return redirect('live:host')

    chat = []
    if session:
        chat = list(session.messages.select_related('user').order_by('created_at')[:100])
    return render(request, 'live/host.html', {
        'session': session,
        'chat_messages': chat,
        'is_host_view': True,
    })


@login_required
@require_POST
def live_chat_post(request, pk):
    session = get_object_or_404(LiveSession, pk=pk)
    text = (request.POST.get('text') or '').strip()[:500]
    if not text:
        messages.error(request, 'Xabar bo‘sh.')
        return redirect('live:watch')
    if session.status != LiveSession.Status.LIVE:
        messages.warning(request, 'Efir jonli emas — chat yopiq.')
        return redirect('live:watch')
    is_teacher = (
        request.user.pk == session.host_id
        or request.user.can_manage_content
    )
    LiveChatMessage.objects.create(
        session=session,
        user=request.user,
        text=text,
        is_from_teacher=is_teacher,
    )
    next_url = request.POST.get('next') or 'live:watch'
    if next_url == 'host':
        return redirect('live:host')
    return redirect('live:watch')
