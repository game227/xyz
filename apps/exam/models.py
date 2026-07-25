"""Exam app models.

Har bir video dars (Lesson) o'zining 10 ta savollik test to'plamiga ega.
Bu chalkashlikni oldini oladi: test = video, bitta-bitta.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import ActivatableModel, OrderedModel, TimeStampedModel
from apps.education.models import Lesson, Topic

from .constants import DEFAULT_PASSING_SCORE, QUESTIONS_PER_LESSON


class Question(TimeStampedModel, ActivatableModel):
    """Savol — aniq bir video dars test to'plamiga bog'langan."""

    class Difficulty(models.TextChoices):
        EASY = 'EASY', 'Oson'
        MEDIUM = 'MEDIUM', "O'rta"
        HARD = 'HARD', 'Qiyin'
        EXPERT = 'EXPERT', 'Ekspert'

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='video dars',
        help_text='Savol shu video darsning 10 talik test to‘plamiga kiradi.',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='mavzu',
        help_text='Avtomatik: lesson.topic',
    )
    text = models.TextField(verbose_name='savol matni')
    explanation = models.TextField(
        blank=True, verbose_name='tushuntirish', help_text="Natija sahifasida ko'rsatiladi."
    )
    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM, verbose_name='qiyinlik'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_questions',
        verbose_name='kim yaratgan',
    )

    class Meta:
        verbose_name = 'Savol'
        verbose_name_plural = 'Savollar'
        ordering = ['id']

    def __str__(self):
        return self.text[:60]

    def clean(self):
        super().clean()
        if self.lesson_id:
            active_count = Question.objects.filter(
                lesson_id=self.lesson_id, is_active=True
            ).exclude(pk=self.pk).count()
            if self.is_active and active_count >= QUESTIONS_PER_LESSON:
                raise ValidationError(
                    f'Har bir video uchun maksimal {QUESTIONS_PER_LESSON} ta faol savol bo‘lishi mumkin.'
                )

    def save(self, *args, **kwargs):
        if self.lesson_id:
            self.topic_id = self.lesson.topic_id
        super().save(*args, **kwargs)

    @property
    def has_valid_answers(self):
        return self.answers.count() >= 4 and self.answers.filter(is_correct=True).count() == 1


class Answer(TimeStampedModel, OrderedModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answers', verbose_name='savol'
    )
    text = models.CharField(max_length=500, verbose_name='javob matni')
    is_correct = models.BooleanField(default=False, verbose_name="to'g'ri javobmi")

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Javob'
        verbose_name_plural = 'Javoblar'

    def __str__(self):
        return f'{self.text} ({"to\'g\'ri" if self.is_correct else "noto\'g\'ri"})'


class ExamSettings(TimeStampedModel):
    """Per-topic default test sozlamalari (o'tish foizi, vaqt).
    Savollar soni har doim QUESTIONS_PER_LESSON — o'zgartirilmaydi.
    """

    topic = models.OneToOneField(
        Topic, on_delete=models.CASCADE, related_name='exam_settings', verbose_name='mavzu'
    )
    question_count = models.PositiveIntegerField(
        default=QUESTIONS_PER_LESSON,
        verbose_name='savollar soni',
        help_text=f'Har bir video uchun qat’iy {QUESTIONS_PER_LESSON} ta.',
    )
    passing_score = models.PositiveIntegerField(
        default=DEFAULT_PASSING_SCORE,
        verbose_name="o'tish foizi (%)",
        help_text='Masalan: 70, 80, 85, 90',
    )
    time_limit_minutes = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='vaqt limiti (daqiqa, ixtiyoriy)'
    )

    class Meta:
        verbose_name = 'Test sozlamasi'
        verbose_name_plural = 'Test sozlamalari'

    def __str__(self):
        return f'{self.topic.title} sozlamasi'

    def save(self, *args, **kwargs):
        self.question_count = QUESTIONS_PER_LESSON
        super().save(*args, **kwargs)


class ExamAttempt(TimeStampedModel):
    """Bitta video dars testi urinishi. Barcha urinishlar saqlanadi."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='exam_attempts', verbose_name='foydalanuvchi',
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='exam_attempts',
        verbose_name='video dars',
    )
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='exam_attempts', verbose_name='mavzu'
    )
    total_questions = models.PositiveIntegerField(verbose_name='savollar soni')
    correct_answers = models.PositiveIntegerField(verbose_name="to'g'ri javoblar")
    wrong_answers = models.PositiveIntegerField(verbose_name="noto'g'ri javoblar")
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='foiz (%)')
    is_passed = models.BooleanField(default=False, verbose_name="o'tdimi")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name='sarflangan vaqt (soniya)')

    class Meta:
        verbose_name = 'Test urinishi'
        verbose_name_plural = 'Test urinishlari'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.lesson} — {self.score}%'

    def save(self, *args, **kwargs):
        if self.lesson_id:
            self.topic_id = self.lesson.topic_id
        super().save(*args, **kwargs)


class ExamAttemptQuestion(models.Model):
    attempt = models.ForeignKey(
        ExamAttempt, on_delete=models.CASCADE, related_name='attempt_questions'
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='attempt_questions'
    )
    selected_answer = models.ForeignKey(
        Answer, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Urinish savoli'
        verbose_name_plural = 'Urinish savollari'
        ordering = ['order']

    def __str__(self):
        return f'{self.attempt_id} — {self.question_id}'
