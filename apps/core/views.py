"""Project-wide views: home, rating, person detail, error handlers."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.accounts.models import CustomUser

from .models import Founder
from .services import (
    get_active_founders,
    get_homepage_teachers,
    get_leaderboard,
    get_student_of_the_month,
)
from .utils import get_logger

logger = get_logger(__name__)


def home(request):
    """Landing — asoschilar/o‘qituvchilar hammaga; reyting faqat login."""
    from apps.education.models import Subject
    from apps.subscription.access import get_freemium_lesson
    from apps.subscription.services import get_active_contacts

    subjects = Subject.objects.filter(is_active=True)[:6]
    student_month = get_student_of_the_month()
    month_board = {'entries': [], 'year': None, 'month': None}
    if request.user.is_authenticated:
        month_board = get_leaderboard(limit=5, period='month')

    return render(request, 'core/home.html', {
        'subjects': subjects,
        'stats': {
            'subjects_count': Subject.objects.filter(is_active=True).count(),
            'teachers_count': len(get_homepage_teachers(limit=50)),
            'founders_count': get_active_founders().count(),
        },
        'free_lesson': get_freemium_lesson(),
        'contacts': get_active_contacts(),
        'founders': get_active_founders(),
        'teachers': get_homepage_teachers(),
        'student_of_month': student_month,
        'leaderboard': month_board['entries'],
        'rating_year': month_board['year'] or (student_month['year'] if student_month else None),
        'rating_month': month_board['month'] or (student_month['month'] if student_month else None),
    })


@login_required
def rating(request):
    """To‘liq reyting — faqat autentifikatsiyadan o‘tgan foydalanuvchilar."""
    period = request.GET.get('period', 'month')
    if period not in ('month', 'all'):
        period = 'month'
    board = get_leaderboard(limit=50, period=period)
    my_rank = next(
        (row for row in board['entries'] if row['user'].pk == request.user.pk),
        None,
    )
    return render(request, 'core/rating.html', {
        'leaderboard': board['entries'],
        'period': period,
        'rating_year': board['year'],
        'rating_month': board['month'],
        'student_of_month': get_student_of_the_month() if period == 'month' else None,
        'my_rank': my_rank,
    })


def founder_detail(request, pk):
    founder = get_object_or_404(Founder, pk=pk, is_active=True)
    return render(request, 'core/person_detail.html', {
        'person_kind': 'founder',
        'person': founder,
        'back_anchor': 'asoschilar',
    })


def teacher_detail(request, pk):
    teacher = get_object_or_404(
        CustomUser,
        pk=pk,
        role=CustomUser.Role.TEACHER,
        is_active=True,
        show_on_homepage=True,
    )
    return render(request, 'core/person_detail.html', {
        'person_kind': 'teacher',
        'person': teacher,
        'back_anchor': 'oqituvchilar',
    })


def error_404(request, exception=None):
    logger.info('404 Not Found: %s', request.path)
    return render(request, 'errors/404.html', status=404)


def error_403(request, exception=None):
    logger.warning('403 Forbidden: %s (user=%s)', request.path, getattr(request.user, 'username', 'anonymous'))
    return render(request, 'errors/403.html', status=403)


def error_500(request):
    logger.error('500 Server Error: %s', request.path)
    return render(request, 'errors/500.html', status=500)
