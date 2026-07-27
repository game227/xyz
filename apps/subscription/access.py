"""Freemium + subscription access rules.

- Belgilangan (is_free_preview) yoki id bo‘yicha barqaror bepul video + 10 talik test.
- Qolgan kontent faol obunani talab qiladi.
- Bepul test natijalari saqlanadi.
"""
from apps.education.models import Lesson

from .services import has_active_subscription

BROWSE_URL_NAMES = {
    'education:subject_list',
    'education:subject_detail',
    'education:course_detail',
    'education:module_detail',
    'education:topic_detail',
    'progress:dashboard',
    'exam:exam_history',
    'exam:exam_result',
}

# Video kamida shu foizgacha ko‘rilishi kerak (yoki tugatildi tugmasi ochiladi).
MIN_WATCH_PERCENT_TO_COMPLETE = 70


def get_freemium_lesson():
    """Barqaror bepul dars: avval pin (is_free_preview), bo‘lmasa eng kichik id."""
    base = (
        Lesson.objects.filter(
            is_active=True,
            topic__is_active=True,
            topic__module__is_active=True,
            topic__module__course__is_active=True,
            topic__module__course__subject__is_active=True,
        )
        .select_related(
            'topic',
            'topic__module',
            'topic__module__course',
            'topic__module__course__subject',
        )
    )
    pinned = base.filter(is_free_preview=True).order_by('id').first()
    if pinned:
        return pinned
    return base.order_by('id').first()


def is_freemium_lesson(lesson):
    free = get_freemium_lesson()
    return bool(free and lesson and free.id == lesson.id)


def can_access_lesson(user, lesson):
    if not user.is_authenticated:
        return False
    if has_active_subscription(user):
        return True
    return is_freemium_lesson(lesson)


def can_access_exam_for_lesson(user, lesson):
    if not user.is_authenticated:
        return False
    if has_active_subscription(user):
        return True
    return is_freemium_lesson(lesson)


def can_start_lesson_exam(user, lesson):
    """Video tugatilgach shu videoning 10 talik testi ochiladi."""
    from apps.progress.models import LessonProgress

    if not can_access_exam_for_lesson(user, lesson):
        return False
    return LessonProgress.objects.filter(
        user=user, lesson=lesson, is_completed=True
    ).exists()


def request_url_name(request):
    match = request.resolver_match
    if not match or not match.namespace or not match.url_name:
        return None
    return f'{match.namespace}:{match.url_name}'


def is_request_allowed_without_subscription(request):
    url_name = request_url_name(request)
    if url_name in BROWSE_URL_NAMES:
        return True

    match = request.resolver_match
    kwargs = match.kwargs if match else {}

    if url_name == 'education:lesson_detail':
        lesson = Lesson.objects.filter(pk=kwargs.get('pk'), is_active=True).first()
        return is_freemium_lesson(lesson)

    if url_name in {
        'progress:mark_lesson_complete',
        'progress:save_watch_progress',
    }:
        lesson = Lesson.objects.filter(pk=kwargs.get('lesson_pk'), is_active=True).first()
        return is_freemium_lesson(lesson)

    if url_name in {
        'exam:exam_start',
        'exam:exam_take',
        'exam:exam_submit',
        'exam:exam_history',
    }:
        lesson = Lesson.objects.filter(pk=kwargs.get('lesson_pk'), is_active=True).first()
        return is_freemium_lesson(lesson)

    return False
