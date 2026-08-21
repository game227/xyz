"""Reyting va oy o‘quvchisi hisoblashlari."""
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Max, Q
from django.utils import timezone

from apps.exam.models import ExamAttempt

from .models import Founder, Notification, StudentOfTheMonth

User = get_user_model()


def notify_user(user, ntype, title, message='', url=''):
    """Bitta foydalanuvchiga bildirishnoma yaratadi."""
    return Notification.objects.create(
        user=user, ntype=ntype, title=title, message=message, url=url,
    )


def notify_many(users, ntype, title, message='', url=''):
    """Bir nechta foydalanuvchiga bir xil bildirishnoma yuboradi (bulk)."""
    notifications = [
        Notification(user=u, ntype=ntype, title=title, message=message, url=url)
        for u in users
    ]
    return Notification.objects.bulk_create(notifications)


def notify_all_active_users(ntype, title, message='', url='', exclude_user_id=None):
    """Barcha faol foydalanuvchilarga bildirishnoma yuboradi (masalan, jonli dars boshlanganda)."""
    qs = User.objects.filter(is_active=True)
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)
    return notify_many(qs, ntype, title, message=message, url=url)


def get_active_founders():
    return Founder.objects.filter(is_active=True).order_by('order', 'id')


def get_homepage_teachers(limit=6):
    """Bosh sahifa uchun o‘qituvchilar."""
    qs = (
        User.objects.filter(
            is_active=True,
            role=User.Role.TEACHER,
            show_on_homepage=True,
        )
        .order_by('homepage_order', 'first_name', 'username')
    )
    teachers = list(qs[:limit])
    if teachers:
        return teachers
    # Fallback: barcha faol o‘qituvchilar
    return list(
        User.objects.filter(is_active=True, role=User.Role.TEACHER)
        .order_by('homepage_order', 'first_name', 'username')[:limit]
    )


def _month_bounds(year=None, month=None):
    now = timezone.localtime()
    year = year or now.year
    month = month or now.month
    start = timezone.make_aware(datetime(year, month, 1))
    if month == 12:
        end = timezone.make_aware(datetime(year + 1, 1, 1))
    else:
        end = timezone.make_aware(datetime(year, month + 1, 1))
    return year, month, start, end


def get_leaderboard(limit=10, year=None, month=None, period='month'):
    """O‘quvchilar reytingi: o‘rtacha ball + urinishlar soni.

    period='month' — joriy oy; period='all' — barcha vaqt.
    """
    qs = ExamAttempt.objects.filter(user__role=User.Role.STUDENT, user__is_active=True)

    if period == 'month':
        year, month, start, end = _month_bounds(year, month)
        qs = qs.filter(created_at__gte=start, created_at__lt=end)
    else:
        year, month = None, None

    rows = (
        qs.values('user_id')
        .annotate(
            avg_score=Avg('score'),
            best_score=Max('score'),
            attempts=Count('id'),
            passed=Count('id', filter=Q(is_passed=True)),
        )
        .order_by('-avg_score', '-best_score', '-attempts')[:limit]
    )

    user_ids = [row['user_id'] for row in rows]
    users = {u.id: u for u in User.objects.filter(id__in=user_ids)}
    leaderboard = []
    for rank, row in enumerate(rows, start=1):
        user = users.get(row['user_id'])
        if not user:
            continue
        leaderboard.append({
            'rank': rank,
            'user': user,
            'avg_score': round(float(row['avg_score'] or 0), 1),
            'best_score': round(float(row['best_score'] or 0), 1),
            'attempts': row['attempts'],
            'passed': row['passed'],
        })
    return {
        'entries': leaderboard,
        'year': year,
        'month': month,
        'period': period,
    }


def get_student_of_the_month(year=None, month=None):
    """Avval admin yozuvi, keyin oy reytingining 1-o‘rini."""
    year, month, _, _ = _month_bounds(year, month)

    manual = (
        StudentOfTheMonth.objects
        .filter(year=year, month=month, is_published=True)
        .select_related('user')
        .first()
    )
    if manual:
        return {
            'user': manual.user,
            'year': year,
            'month': month,
            'highlight': manual.highlight or 'Oy o‘quvchisi',
            'source': 'manual',
            'stats': None,
        }

    board = get_leaderboard(limit=1, year=year, month=month, period='month')
    if not board['entries']:
        return None

    top = board['entries'][0]
    return {
        'user': top['user'],
        'year': year,
        'month': month,
        'highlight': f"O‘rtacha {top['avg_score']}% · {top['attempts']} ta test",
        'source': 'rating',
        'stats': top,
    }
