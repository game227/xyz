"""Education models.

Confirmed hierarchy (do not change — see project decisions log):
    Subject -> Course -> Module -> Topic -> Lesson

Question/Answer/ExamAttempt live in apps.exam and point back to Topic.
LessonProgress/TopicProgress live in apps.progress and point back here.
"""
from django.db import models

from apps.core.models import ActivatableModel, OrderedModel, TimeStampedModel


class Subject(TimeStampedModel, ActivatableModel):
    """Top-level subject, e.g. Matematika, Fizika, Ingliz tili."""

    name = models.CharField(max_length=150, unique=True, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')
    image = models.ImageField(upload_to='subjects/', blank=True, null=True, verbose_name='rasm')

    class Meta:
        verbose_name = 'Fan'
        verbose_name_plural = 'Fanlar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(TimeStampedModel, ActivatableModel, OrderedModel):
    """A course within a subject, e.g. Matematika -> Algebra kursi."""

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='courses', verbose_name='fan'
    )
    title = models.CharField(max_length=200, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')
    image = models.ImageField(upload_to='courses/', blank=True, null=True, verbose_name='rasm')

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'

    def __str__(self):
        return f'{self.subject.name} — {self.title}'


class Module(TimeStampedModel, ActivatableModel, OrderedModel):
    """A module groups related topics within a course."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='modules', verbose_name='kurs'
    )
    title = models.CharField(max_length=200, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Modul'
        verbose_name_plural = 'Modullar'

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Topic(TimeStampedModel, ActivatableModel, OrderedModel):
    """The central model of the platform — lessons, questions, results and
    progress all key off Topic."""

    class Difficulty(models.TextChoices):
        EASY = 'EASY', 'Oson'
        MEDIUM = 'MEDIUM', "O'rta"
        HARD = 'HARD', 'Qiyin'
        EXPERT = 'EXPERT', 'Ekspert'

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name='topics', verbose_name='modul'
    )
    title = models.CharField(max_length=200, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')
    difficulty_level = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM,
        verbose_name='qiyinlik darajasi (curriculum uchun)',
        help_text="Bu mavzuning umumiy darajasi. Savol tanlashda ishlatilmaydi — faqat o'quv dasturini tashkil qilish uchun.",
    )

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Mavzu'
        verbose_name_plural = 'Mavzular'

    def __str__(self):
        return f'{self.module.title} — {self.title}'


class Lesson(TimeStampedModel, ActivatableModel, OrderedModel):
    """A single video lesson within a topic."""

    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='lessons', verbose_name='mavzu'
    )
    title = models.CharField(max_length=200, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')
    video = models.FileField(upload_to='videos/', verbose_name='video fayl')
    pdf_material = models.FileField(
        upload_to='pdfs/', blank=True, null=True, verbose_name="qo'shimcha material (PDF)"
    )
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name='davomiyligi (daqiqa)')
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_lessons',
        verbose_name='kim yaratgan',
    )

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Video dars'
        verbose_name_plural = 'Video darslar'

    def __str__(self):
        return f'{self.topic.title} — {self.title}'
