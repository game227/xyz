from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.core.services import notify_all_active_users

from .models import LiveSession


def live_watch(request):
    """Jonli dars — mehmon va login qilganlar ko‘radi (YouTube/Telegram havolasi)."""
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
    return render(request, 'live/watch.html', {
        'session': session,
        'is_host_view': False,
    })


@login_required
def live_host(request):
    """O‘qituvchi/admin efirni boshqaradi: sarlavha + havola qo‘yib faollashtiradi."""
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
            title = (request.POST.get('title') or '').strip()[:200] or 'Jonli matematika darsi'
            platform = request.POST.get('platform') or LiveSession.Platform.YOUTUBE
            if platform not in LiveSession.Platform.values:
                platform = LiveSession.Platform.YOUTUBE
            stream_url = (request.POST.get('stream_url') or '').strip()[:200]
            if not stream_url:
                messages.error(request, 'Efir havolasini kiriting (YouTube yoki Telegram).')
                return redirect('live:host')
            with transaction.atomic():
                # select_for_update — ikkita tez ketma-ket bosishda ikkita efir ochilib
                # qolmasligi uchun (masalan formani ikki marta bosib yuborilsa).
                existing = (
                    LiveSession.objects.select_for_update()
                    .filter(host=user, status=LiveSession.Status.LIVE)
                    .order_by('-started_at')
                    .first()
                )
                if existing:
                    session = existing
                    messages.info(request, 'Sizda allaqachon jonli efir bor.')
                else:
                    session = LiveSession.objects.create(
                        title=title,
                        host=user,
                        platform=platform,
                        stream_url=stream_url,
                    )
                    session.mark_live()
                    messages.success(request, 'Jonli efir boshlandi va foydalanuvchilarga xabar yuborildi.')
                    notify_all_active_users(
                        ntype='LIVE_STARTED',
                        title=f'Jonli dars boshlandi: {session.title}',
                        message=f'{user.get_full_name() or user.username} jonli dars boshladi. Efirga o‘tish uchun bosing.',
                        url=reverse('live:watch'),
                        exclude_user_id=user.pk,
                    )
            return redirect('live:host')
        if action == 'end' and session:
            session.mark_ended()
            messages.success(request, 'Efir yakunlandi.')
            return redirect('live:host')

    return render(request, 'live/host.html', {
        'session': session,
        'is_host_view': True,
        'platform_choices': LiveSession.Platform.choices,
    })
