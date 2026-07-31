"""Shared abstract base models.

Every model across the project should inherit TimeStampedModel so that
created_at / updated_at are always present, per project convention.
ActivatableModel is opt-in and only mixed in where an is_active toggle
makes sense (Subject, Course, Topic, Lesson, Question, ...).
"""
from django.db import models


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at to any model that inherits it."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='yangilangan sana')

    class Meta:
        abstract = True


class ActivatableModel(models.Model):
    """Adds an is_active toggle for soft enable/disable without deleting rows."""

    is_active = models.BooleanField(default=True, verbose_name='faol')

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    """Adds an `order` field for models that need manual, admin-controlled ordering."""

    order = models.PositiveIntegerField(default=0, verbose_name='tartib')

    class Meta:
        abstract = True
        ordering = ['order']


class Founder(TimeStampedModel, ActivatableModel, OrderedModel):
    """Platforma asoschilari — bosh sahifada ko‘rsatiladi (admin CRUD)."""

    full_name = models.CharField(max_length=120, verbose_name="to‘liq ism")
    role_title = models.CharField(
        max_length=120,
        verbose_name='lavozim',
        help_text='Masalan: Asoschi, CEO, Hammuassis',
    )
    bio = models.TextField(blank=True, verbose_name='qisqa bio')
    full_bio = models.TextField(
        blank=True,
        verbose_name="to‘liq ma'lumot",
        help_text='Batafsil sahifada chiqadi',
    )
    education = models.CharField(max_length=255, blank=True, verbose_name="ta'lim")
    achievements = models.TextField(blank=True, verbose_name='yutuqlar')
    email = models.EmailField(blank=True, verbose_name='email')
    photo = models.ImageField(
        upload_to='founders/', blank=True, null=True, verbose_name='rasm'
    )
    telegram = models.CharField(max_length=120, blank=True, verbose_name='Telegram')
    linkedin_url = models.URLField(blank=True, verbose_name='LinkedIn')

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Asoschi'
        verbose_name_plural = 'Asoschilar'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.full_name} — {self.role_title}'


class SiteSettings(TimeStampedModel):
    """Singleton: logo, hero video va sayt sozlamalari."""

    site_name = models.CharField(
        max_length=80, default='XYZ', verbose_name='sayt nomi',
    )
    tagline = models.CharField(
        max_length=200,
        blank=True,
        default='Faqat matematika — universitet imtihoniga onlayn tayyorgarlik',
        verbose_name='qisqa tavsif',
    )
    logo = models.ImageField(
        upload_to='branding/',
        blank=True,
        null=True,
        verbose_name='logo',
        help_text='PNG/SVG/JPG — navbar va admin paneldа ko‘rinadi.',
    )
    favicon = models.ImageField(
        upload_to='branding/',
        blank=True,
        null=True,
        verbose_name='favicon',
        help_text='Ixtiyoriy: brauzer tab ikonkasi (32×32 yoki 64×64).',
    )
    hero_video = models.FileField(
        upload_to='hero/',
        blank=True,
        null=True,
        verbose_name='bosh sahifa video',
        help_text='Ovozsiz, avtomatik aylanish. Controls yo‘q.',
    )
    hero_video_active = models.BooleanField(
        default=True,
        verbose_name='hero video faol',
    )

    class Meta:
        verbose_name = 'Sayt sozlamasi'
        verbose_name_plural = 'Sayt sozlamalari'

    def __str__(self):
        return 'Sayt sozlamalari'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class StudentOfTheMonth(TimeStampedModel):
    """Admin belgilagan oy o‘quvchisi. Bo‘sh qolsa — reytingdan avtomatik olinadi."""

    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='month_awards',
        verbose_name='o‘quvchi',
    )
    year = models.PositiveIntegerField(verbose_name='yil')
    month = models.PositiveIntegerField(verbose_name='oy')
    highlight = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='izoh',
        help_text='Masalan: Eng faol va yuqori natijali o‘quvchi',
    )
    is_published = models.BooleanField(default=True, verbose_name='nashr qilingan')

    class Meta:
        verbose_name = 'Oy o‘quvchisi'
        verbose_name_plural = 'Oy o‘quvchilari'
        unique_together = ('year', 'month')
        ordering = ['-year', '-month']

    def __str__(self):
        return f'{self.year}-{self.month:02d}: {self.user}'
