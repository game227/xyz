"""Jonli efir + chat modellari."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class LiveSession(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Rejalashtirilgan'
        LIVE = 'LIVE', 'Jonli'
        ENDED = 'ENDED', 'Tugagan'

    title = models.CharField(max_length=200, verbose_name='sarlavha')
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_live_sessions',
        verbose_name='o‘qituvchi',
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


class LiveChatMessage(TimeStampedModel):
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
