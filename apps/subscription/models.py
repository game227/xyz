"""Subscription model.

No online payment in the MVP — admins activate subscriptions by hand
(see admin.py actions). Expiry is checked lazily (is_currently_active)
rather than via a cron job, which is simpler and always correct.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Subscription(TimeStampedModel):

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Faol'
        EXPIRED = 'EXPIRED', 'Muddati tugagan'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='subscriptions', verbose_name='foydalanuvchi',
    )
    start_date = models.DateField(verbose_name='boshlanish sanasi')
    end_date = models.DateField(verbose_name='tugash sanasi')
    duration_days = models.PositiveIntegerField(verbose_name='davomiyligi (kun)')
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE, verbose_name='holati'
    )
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activated_subscriptions', verbose_name='kim tomonidan faollashtirilgan',
    )

    class Meta:
        verbose_name = 'Obuna'
        verbose_name_plural = 'Obunalar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.start_date} → {self.end_date} ({self.status})'

    def refresh_status(self):
        """Flip ACTIVE -> EXPIRED once end_date has passed. Called on
        every read via is_currently_active, so status is always correct
        without needing a scheduled task."""
        if self.status == self.Status.ACTIVE and self.end_date < timezone.localdate():
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status', 'updated_at'])

    def is_currently_active(self):
        self.refresh_status()
        return self.status == self.Status.ACTIVE and self.end_date >= timezone.localdate()


class ContactChannel(TimeStampedModel):
    """Admin panel orqali boshqariladigan bog‘lanish kontaktlari."""

    class ChannelType(models.TextChoices):
        PHONE = 'PHONE', 'Telefon'
        EMAIL = 'EMAIL', 'Email'
        TELEGRAM = 'TELEGRAM', 'Telegram'
        INSTAGRAM = 'INSTAGRAM', 'Instagram'
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        OTHER = 'OTHER', 'Boshqa'

    label = models.CharField(max_length=80, verbose_name='sarlavha')
    channel_type = models.CharField(
        max_length=20, choices=ChannelType.choices, default=ChannelType.OTHER,
        verbose_name='turi',
    )
    value = models.CharField(
        max_length=255, verbose_name='qiymat',
        help_text='Masalan: +99890..., hello@xyz.uz, @username',
    )
    url = models.URLField(
        blank=True, verbose_name='havola',
        help_text='Ixtiyoriy: bosilganda ochiladigan to‘liq URL',
    )
    icon = models.CharField(
        max_length=40, blank=True, verbose_name='ikonka',
        help_text='Bootstrap Icons nomi, masalan: bi-telegram, bi-envelope',
    )
    order = models.PositiveIntegerField(default=0, verbose_name='tartib')
    is_active = models.BooleanField(default=True, verbose_name='faol')
    note = models.CharField(max_length=200, blank=True, verbose_name='izoh')

    class Meta:
        verbose_name = 'Kontakt'
        verbose_name_plural = 'Kontaktlar'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.label}: {self.value}'

    @property
    def href(self):
        if self.url:
            return self.url
        if self.channel_type == self.ChannelType.EMAIL:
            return f'mailto:{self.value}'
        if self.channel_type == self.ChannelType.PHONE:
            return f'tel:{self.value.replace(" ", "")}'
        if self.channel_type == self.ChannelType.TELEGRAM:
            handle = self.value.lstrip('@')
            return f'https://t.me/{handle}'
        if self.channel_type == self.ChannelType.WHATSAPP:
            digits = ''.join(ch for ch in self.value if ch.isdigit())
            return f'https://wa.me/{digits}' if digits else ''
        if self.channel_type == self.ChannelType.INSTAGRAM:
            handle = self.value.lstrip('@')
            return f'https://instagram.com/{handle}'
        return ''

    @property
    def bootstrap_icon(self):
        if self.icon:
            return self.icon if self.icon.startswith('bi-') else f'bi-{self.icon}'
        defaults = {
            self.ChannelType.PHONE: 'bi-telephone',
            self.ChannelType.EMAIL: 'bi-envelope',
            self.ChannelType.TELEGRAM: 'bi-telegram',
            self.ChannelType.INSTAGRAM: 'bi-instagram',
            self.ChannelType.WHATSAPP: 'bi-whatsapp',
            self.ChannelType.OTHER: 'bi-link-45deg',
        }
        return defaults.get(self.channel_type, 'bi-link-45deg')
