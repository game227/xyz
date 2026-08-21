"""Progress services.

Two things are stored (LessonProgress, TopicProgress); everything above
Topic (Module/Course/Subject/overall) is computed here on read, from
those two tables — see models.py docstring for why.
"""
from django.db.models import Avg, Count
from django.utils import timezone

from apps.core.utils import get_logger
from apps.education.models import Course, Topic

from .models import LessonProgress, TopicProgress

logger = get_logger('progress')


# ---------------------------------------------------------------------------
# Lesson-level
# ---------------------------------------------------------------------------

def mark_lesson_complete(user, lesson, *, require_watch=True):
    from apps.subscription.access import MIN_WATCH_PERCENT_TO_COMPLETE

    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    if require_watch and progress.watch_percent < MIN_WATCH_PERCENT_TO_COMPLETE:
        return progress, False
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
        logger.info('LESSON_COMPLETED: user=%s lesson=%s', user.username, lesson.title)
    return progress, True


def save_watch_progress(user, lesson, percent):
    percent = max(0, min(100, int(percent)))
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    if percent > progress.watch_percent:
        progress.watch_percent = percent
        progress.save(update_fields=['watch_percent', 'updated_at'])
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
    from apps.education.models import Subject

    last_lesson_progress = (
        LessonProgress.objects
        .filter(user=user)
        .select_related('lesson', 'lesson__topic')
        .order_by('-updated_at')
        .first()
    )
    recent_attempts = user.exam_attempts.select_related('topic', 'lesson').order_by('-created_at')[:5]
    completed_topics_count = TopicProgress.objects.filter(user=user, is_completed=True).count()

    subject_rows = []
    for subject in Subject.objects.filter(is_active=True).order_by('name'):
        courses = list(subject.courses.filter(is_active=True))
        course_rows = [
            {
                'course': course,
                'percent': course_progress_percent(user, course),
            }
            for course in courses
        ]
        subject_rows.append({
            'subject': subject,
            'percent': subject_progress_percent(user, subject),
            'courses': course_rows,
        })

    progress_chart = _monthly_progress_chart(user)
    weekly_chart = _weekly_progress_chart(user)

    return {
        'overall_progress': overall_progress_percent(user),
        'completed_topics_count': completed_topics_count,
        'last_lesson': last_lesson_progress.lesson if last_lesson_progress else None,
        'recent_attempts': recent_attempts,
        'subject_progress': subject_rows,
        'progress_chart': progress_chart,
        'weekly_chart': weekly_chart,
        'has_chart_data': bool(progress_chart) or any(
            p['attempts'] or p['lessons_completed'] for p in weekly_chart
        ),
    }


def _monthly_progress_chart(user):
    """Oxirgi 6 oy — o‘rtacha test balli va urinishlar soni."""
    import datetime

    from django.db.models.functions import TruncMonth

    from apps.exam.models import ExamAttempt

    month_stats = (
        ExamAttempt.objects.filter(user=user)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(avg_score=Avg('score'), attempts=Count('id'))
        .order_by('month')
    )
    by_month = {}
    for row in month_stats:
        if not row['month']:
            continue
        key = row['month'].date() if hasattr(row['month'], 'date') else row['month']
        by_month[key] = {
            'avg_score': round(float(row['avg_score'] or 0), 1),
            'attempts': row['attempts'],
        }

    today = timezone.localdate().replace(day=1)
    chart = []
    for i in range(5, -1, -1):
        # Go back i months from current month start
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        key = datetime.date(year, month, 1)
        data = by_month.get(key, {'avg_score': 0, 'attempts': 0})
        if data['attempts'] or key in by_month:
            chart.append({
                'label': key.strftime('%m.%Y'),
                'avg_score': data['avg_score'],
                'attempts': data['attempts'],
            })
    # Only months that had activity (keep chart clean); fall back to empty
    return [p for p in chart if p['attempts']]


def _weekly_progress_chart(user):
    """Oxirgi 8 hafta — urinishlar, o‘rtacha ball, tugatilgan darslar (bo‘sh haftalar ham)."""
    import datetime

    from django.db.models.functions import TruncWeek

    from apps.exam.models import ExamAttempt

    today = timezone.localdate()
    # ISO week start (Monday)
    week_start = today - datetime.timedelta(days=today.weekday())
    window_start = week_start - datetime.timedelta(weeks=7)

    attempt_rows = (
        ExamAttempt.objects.filter(user=user, created_at__date__gte=window_start)
        .annotate(week=TruncWeek('created_at'))
        .values('week')
        .annotate(avg_score=Avg('score'), attempts=Count('id'))
    )
    attempts_by_week = {}
    for row in attempt_rows:
        if not row['week']:
            continue
        key = row['week'].date() if hasattr(row['week'], 'date') else row['week']
        attempts_by_week[key] = {
            'avg_score': round(float(row['avg_score'] or 0), 1),
            'attempts': row['attempts'],
        }

    lesson_rows = (
        LessonProgress.objects.filter(
            user=user,
            is_completed=True,
            completed_at__isnull=False,
            completed_at__date__gte=window_start,
        )
        .annotate(week=TruncWeek('completed_at'))
        .values('week')
        .annotate(lessons_completed=Count('id'))
    )
    lessons_by_week = {}
    for row in lesson_rows:
        if not row['week']:
            continue
        key = row['week'].date() if hasattr(row['week'], 'date') else row['week']
        lessons_by_week[key] = row['lessons_completed']

    chart = []
    for i in range(7, -1, -1):
        key = week_start - datetime.timedelta(weeks=i)
        att = attempts_by_week.get(key, {'avg_score': 0, 'attempts': 0})
        chart.append({
            'label': key.strftime('%d.%m'),
            'avg_score': att['avg_score'],
            'attempts': att['attempts'],
            'lessons_completed': lessons_by_week.get(key, 0),
        })
    return chart
