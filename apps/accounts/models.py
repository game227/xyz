"""Accounts models.

CustomUser is the single source of truth for identity + role.
Role lives as a simple choices field on the user (not a separate model) —
per project rule: keep MVP simple, only Student/Admin exist today,
Teacher/Moderator are reserved for later without needing a migration
to change the field type.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel


class CustomUser(AbstractUser, TimeStampedModel):

    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'O‘quvchi'
        ADMIN = 'ADMIN', 'Administrator'
        # Reserved for future phases — do not remove, keeps migrations stable:
        TEACHER = 'TEACHER', 'O‘qituvchi'
        MODERATOR = 'MODERATOR', 'Moderator'

    # Istalgan login nomi (Django default ASCII/unicode cheklovi olib tashlangan)
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='login',
        help_text='Istalgan nom — 150 belgigacha.',
        error_messages={'unique': 'Bu login allaqachon band.'},
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name='rol',
    )
    phone_number = models.CharField(max_length=20, blank=True, verbose_name='telefon raqami')
    avatar = models.ImageField(
        upload_to='avatars/', blank=True, null=True, verbose_name='profil rasmi'
    )
    specialty = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='mutaxassislik',
        help_text='O‘qituvchilar uchun: masalan Algebra, Geometriya',
    )
    bio = models.TextField(blank=True, verbose_name='qisqa bio')
    full_bio = models.TextField(
        blank=True,
        verbose_name="to‘liq ma'lumot",
        help_text='Batafsil sahifada chiqadi (asosiy o‘qituvchilar uchun)',
    )
    education = models.CharField(max_length=255, blank=True, verbose_name="ta'lim")
    achievements = models.TextField(blank=True, verbose_name='yutuqlar')
    telegram = models.CharField(max_length=120, blank=True, verbose_name='Telegram')
    show_on_homepage = models.BooleanField(
        default=False,
        verbose_name='bosh sahifada ko‘rsatish',
        help_text='O‘qituvchini landing sahifada chiqarish',
    )
    homepage_order = models.PositiveIntegerField(default=0, verbose_name='bosh sahifa tartibi')

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_admin_role(self):
        # Named *_role to avoid clashing with Django's built-in is_staff/is_superuser checks.
        return self.role == self.Role.ADMIN

    @property
    def can_manage_content(self):
        """Teachers and admins can manage lessons/tests on the website."""
        return self.role in {self.Role.TEACHER, self.Role.ADMIN} or self.is_superuser


class TeacherRating(TimeStampedModel):
    """O‘quvchi o‘qituvchiga 1–5 yulduz baho beradi."""

    student = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='given_teacher_ratings',
        verbose_name='o‘quvchi',
    )
    teacher = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='received_teacher_ratings',
        verbose_name='o‘qituvchi',
    )
    lesson = models.ForeignKey(
        'education.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher_ratings',
        verbose_name='dars',
    )
    stars = models.PositiveSmallIntegerField(
        verbose_name='yulduz',
        help_text='1 dan 5 gacha',
    )
    comment = models.CharField(max_length=300, blank=True, verbose_name='izoh')

    class Meta:
        verbose_name = 'O‘qituvchi bahosi'
        verbose_name_plural = 'O‘qituvchi baholari'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'teacher', 'lesson'],
                name='uniq_student_teacher_lesson_rating',
            ),
            models.CheckConstraint(
                check=models.Q(stars__gte=1) & models.Q(stars__lte=5),
                name='teacher_rating_stars_1_5',
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if self.stars is not None and not (1 <= int(self.stars) <= 5):
            raise ValidationError({'stars': 'Baholash 1 dan 5 gacha bo‘lishi kerak.'})
        if self.teacher_id and self.student_id and self.teacher_id == self.student_id:
            raise ValidationError('O‘zini o‘zi baholab bo‘lmaydi.')

    def __str__(self):
        return f'{self.teacher} ← {self.stars}★'
