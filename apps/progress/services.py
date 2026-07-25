"""Progress services.

Two things are stored (LessonProgress, TopicProgress); everything above
Topic (Module/Course/Subject/overall) is computed here on read, from
those two tables — see models.py docstring for why.
"""
from django.utils import timezone

from apps.core.utils import get_logger
from apps.education.models import Course, Topic

from .models import LessonProgress, TopicProgress

logger = get_logger('progress')


# ---------------------------------------------------------------------------
# Lesson-level
# ---------------------------------------------------------------------------

def mark_lesson_complete(user, lesson):
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
        logger.info('LESSON_COMPLETED: user=%s lesson=%s', user.username, lesson.title)
    return progress


def all_lessons_completed(user, topic):
    """Gate used before allowing a student to start the topic's exam —
    per project decision this is a HARD gate, not optional."""
    lesson_ids = set(topic.lessons.filter(is_active=True).values_list('id', flat=True))
    if not lesson_ids:
        return False
    completed_ids = set(
        LessonProgress.objects.filter(
            user=user, lesson_id__in=lesson_ids, is_completed=True
        ).values_list('lesson_id', flat=True)
    )
    return lesson_ids.issubset(completed_ids)


# ---------------------------------------------------------------------------
# Topic-level
# ---------------------------------------------------------------------------

def update_topic_progress(user, topic, score, passed):
    """Legacy helper — prefer update_topic_progress_from_lesson_exam."""
    progress, _ = TopicProgress.objects.get_or_create(user=user, topic=topic)

    if score > progress.best_score:
        progress.best_score = score

    if passed and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        logger.info('TOPIC_COMPLETED: user=%s topic=%s score=%s', user.username, topic.title, score)

    progress.save(update_fields=['best_score', 'is_completed', 'completed_at', 'updated_at'])
    return progress


def update_topic_progress_from_lesson_exam(user, lesson, score, passed):
    """Har bir video testi natijasidan mavzu progressini yangilaydi.

    Mavzu tugallangan hisoblanadi: undagi barcha faol videolar uchun
    kamida bitta o'tilgan (passed) test urinishi bo'lsa.
    best_score = mavzudagi eng yaxshi video-test foizi.
    """
    from apps.exam.models import ExamAttempt

    topic = lesson.topic
    progress, _ = TopicProgress.objects.get_or_create(user=user, topic=topic)

    if score > progress.best_score:
        progress.best_score = score

    lesson_ids = list(topic.lessons.filter(is_active=True).values_list('id', flat=True))
    if lesson_ids:
        passed_lesson_ids = set(
            ExamAttempt.objects.filter(
                user=user, lesson_id__in=lesson_ids, is_passed=True
            ).values_list('lesson_id', flat=True)
        )
        all_passed = set(lesson_ids).issubset(passed_lesson_ids)
    else:
        all_passed = False

    if all_passed and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        logger.info(
            'TOPIC_COMPLETED: user=%s topic=%s via lesson exams',
            user.username, topic.title,
        )

    progress.save(update_fields=['best_score', 'is_completed', 'completed_at', 'updated_at'])
    return progress


# ---------------------------------------------------------------------------
# Computed roll-ups (Module / Course / Subject / overall)
# ---------------------------------------------------------------------------

def _percent(done, total):
    if total == 0:
        return 0
    return round((done / total) * 100, 1)


def module_progress_percent(user, module):
    topic_ids = list(module.topics.filter(is_active=True).values_list('id', flat=True))
    if not topic_ids:
        return 0
    completed = TopicProgress.objects.filter(
        user=user, topic_id__in=topic_ids, is_completed=True
    ).count()
    return _percent(completed, len(topic_ids))


def course_progress_percent(user, course):
    topic_ids = list(
        Topic.objects.filter(module__course=course, is_active=True).values_list('id', flat=True)
    )
    if not topic_ids:
        return 0
    completed = TopicProgress.objects.filter(
        user=user, topic_id__in=topic_ids, is_completed=True
    ).count()
    return _percent(completed, len(topic_ids))


def subject_progress_percent(user, subject):
    """Per spec: Subject progress = fully-completed courses / total courses."""
    courses = list(Course.objects.filter(subject=subject, is_active=True))
    if not courses:
        return 0
    completed_courses = sum(
        1 for course in courses if course_progress_percent(user, course) == 100
    )
    return _percent(completed_courses, len(courses))


def overall_progress_percent(user):
    """Platform-wide progress: completed topics / total active topics."""
    total_topics = Topic.objects.filter(is_active=True).count()
    if total_topics == 0:
        return 0
    completed_topics = TopicProgress.objects.filter(user=user, is_completed=True).count()
    return _percent(completed_topics, total_topics)


def get_dashboard_context(user):
    """Aggregate everything the student dashboard needs in one call."""
    last_lesson_progress = (
        LessonProgress.objects
        .filter(user=user)
        .select_related('lesson', 'lesson__topic')
        .order_by('-updated_at')
        .first()
    )
    recent_attempts = user.exam_attempts.select_related('topic', 'lesson').order_by('-created_at')[:5]
    completed_topics_count = TopicProgress.objects.filter(user=user, is_completed=True).count()

    return {
        'overall_progress': overall_progress_percent(user),
        'completed_topics_count': completed_topics_count,
        'last_lesson': last_lesson_progress.lesson if last_lesson_progress else None,
        'recent_attempts': recent_attempts,
    }
