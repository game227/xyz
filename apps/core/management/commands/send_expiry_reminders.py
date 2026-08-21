"""Har kuni ishga tushiriladigan buyruq: tugashiga 5 va 1 kun qolgan faol
obunalar egalariga bildirishnoma (va email) yuboradi.

Ishga tushirish: python manage.py send_expiry_reminders
Tavsiya: kuniga bir marta (masalan, ertalab) cron/Render Cron Job orqali.
"""
import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from apps.core.services import notify_user
from apps.subscription.models import Subscription

REMINDER_5_DAYS = 5
REMINDER_1_DAY = 1


class Command(BaseCommand):
    help = 'Tugashiga 5 va 1 kun qolgan faol obunalar uchun bildirishnoma/email yuboradi.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        sent_5 = self._send_window(
            today=today,
            days_before=REMINDER_5_DAYS,
            field='expiry_reminder_sent_at',
            title='Obunangiz tugashiga 5 kun qoldi',
            message_tpl=(
                'Obunangiz {end} sanada tugaydi. '
                'Uzluksiz foydalanish uchun oldindan uzaytiring.'
            ),
        )
        sent_1 = self._send_window(
            today=today,
            days_before=REMINDER_1_DAY,
            field='expiry_final_reminder_sent_at',
            title='Obunangiz ertaga tugaydi',
            message_tpl=(
                'Obunangiz {end} sanada tugaydi (1 kun qoldi). '
                'Kontentga kirish uzilmasligi uchun hozir uzaytiring.'
            ),
        )
        self.stdout.write(self.style.SUCCESS(
            f'5 kunlik: {sent_5} ta, 1 kunlik: {sent_1} ta eslatma yuborildi.'
        ))

    def _send_window(self, *, today, days_before, field, title, message_tpl):
        target_date = today + datetime.timedelta(days=days_before)
        filter_kwargs = {
            'status': Subscription.Status.ACTIVE,
            'end_date': target_date,
            f'{field}__isnull': True,
        }
        subscriptions = (
            Subscription.objects.filter(**filter_kwargs).select_related('user')
        )
        url = reverse('subscription:info')
        sent = 0
        for sub in subscriptions:
            if not sub.is_currently_active():
                continue
            message = message_tpl.format(end=sub.end_date.strftime('%d.%m.%Y'))
            notify_user(
                sub.user,
                ntype='SUB_EXPIRING',
                title=title,
                message=message,
                url=url,
            )
            self._send_email(sub.user, title, message, url)
            setattr(sub, field, timezone.now())
            sub.save(update_fields=[field, 'updated_at'])
            sent += 1
        return sent

    def _send_email(self, user, title, message, url_path):
        email = (getattr(user, 'email', '') or '').strip()
        if not email:
            return
        body = f'{message}\n\nObuna sahifasi: {url_path}\n'
        try:
            send_mail(
                subject=f'XYZ — {title}',
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            # Console/SMTP xatosi buyruqni to‘xtatmasin
            pass
