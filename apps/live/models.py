"""Jonli efir + chat modellari."""
import re

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

# youtube.com/watch?v=ID, youtu.be/ID, youtube.com/live/ID,
# youtube.com/embed/ID, youtube.com/shorts/ID kabi formatlarni qo'llab-quvvatlaydi.
_YOUTUBE_ID_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|live/|embed/|shorts/)|youtu\.be/)'
    r'([A-Za-z0-9_-]{11})'
)


def extract_youtube_id(url):
    """URL ichidan YouTube video ID'ni ajratib oladi, topilmasa None qaytaradi."""
    if not url:
        return None
    match = _YOUTUBE_ID_RE.search(url)
    return match.group(1) if match else None


class LiveSession(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Rejalashtirilgan'
        LIVE = 'LIVE', 'Jonli'
        ENDED = 'ENDED', 'Tugagan'

    class Platform(models.TextChoices):
        YOUTUBE = 'YOUTUBE', 'YouTube'
        TELEGRAM = 'TELEGRAM', 'Telegram'

    title = models.CharField(max_length=200, verbose_name='sarlavha')
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_live_sessions',
        verbose_name='o‘qituvchi',
    )
    platform = models.CharField(
        max_length=20,
        choices=Platform.choices,
        default=Platform.YOUTUBE,
        verbose_name='platforma',
    )
    stream_url = models.URLField(
        verbose_name='efir havolasi',
        help_text='YouTube jonli efir yoki Telegram kanal/efir havolasi.',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name='holat',
    )
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='boshlangan')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='tugagan')

    class Meta:
        verbose_name = 'Jonli efir'
        verbose_name_plural = 'Jonli efirlar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    def mark_live(self):
        self.status = self.Status.LIVE
        self.started_at = timezone.now()
        self.ended_at = None
        self.save(update_fields=['status', 'started_at', 'ended_at', 'updated_at'])

    def mark_ended(self):
        self.status = self.Status.ENDED
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at', 'updated_at'])

    @property
    def youtube_embed_url(self):
        """YouTube bo'lsa va ID ajratilsa — platforma ichida ko'rsatish uchun embed havola.

        Telegram uchun har doim None (Telegram jonli efirlarini iframe orqali
        ko'rsatib bo'lmaydi — foydalanuvchi tashqi havola orqali o'tadi).
        """
        if self.platform != self.Platform.YOUTUBE:
            return None
        video_id = extract_youtube_id(self.stream_url)
        if not video_id:
            return None
        return f'https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0'


class LiveChatMessage(TimeStampedModel):
    """Eski jonli chat yozuvlari — endi UI'da ko‘rsatilmaydi, faqat tarix uchun saqlanadi."""

    session = models.ForeignKey(
        LiveSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='efir',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='live_chat_messages',
        verbose_name='foydalanuvchi',
    )
    text = models.CharField(max_length=500, verbose_name='matn')
    is_from_teacher = models.BooleanField(default=False, verbose_name='o‘qituvchi javobi')

    class Meta:
        verbose_name = 'Jonli chat xabari'
        verbose_name_plural = 'Jonli chat xabarlari'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user}: {self.text[:40]}'
