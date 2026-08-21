"""Project-wide views: home, rating, person detail, error handlers."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import CustomUser, TeacherRating

from .models import Founder, SiteSettings
from .services import (
    get_active_founders,
    get_homepage_teachers,
    get_leaderboard,
    get_student_of_the_month,
)
from .utils import get_logger

logger = get_logger(__name__)


def home(request):
    """Landing — asoschilar/o‘qituvchilar hammaga; reyting guest=3, login=5."""
    from apps.education.models import Subject
    from apps.subscription.access import get_freemium_lesson
    from apps.subscription.services import get_active_contacts

    subjects = Subject.objects.filter(is_active=True)[:6]
    student_month = get_student_of_the_month()
    limit = 5 if request.user.is_authenticated else 3
    month_board = get_leaderboard(limit=limit, period='month')

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
        'site_settings': SiteSettings.load(),
    })


def rating(request):
    """O‘quvchi reytingi — guest top-3, login to‘liq."""
    period = request.GET.get('period', 'month')
    if period not in ('month', 'all'):
        period = 'month'
    limit = 50 if request.user.is_authenticated else 3
    board = get_leaderboard(limit=limit, period=period)
    my_rank = None
    if request.user.is_authenticated:
        full = get_leaderboard(limit=500, period=period)
        my_rank = next(
            (row for row in full['entries'] if row['user'].pk == request.user.pk),
            None,
        )
    return render(request, 'core/rating.html', {
        'leaderboard': board['entries'],
        'period': period,
        'rating_year': board['year'],
        'rating_month': board['month'],
        'student_of_month': get_student_of_the_month() if period == 'month' else None,
        'my_rank': my_rank,
        'is_partial': not request.user.is_authenticated,
    })


@login_required
def teacher_rating_list(request):
    """O‘qituvchilar reytingi — faqat login."""
    teachers = (
        CustomUser.objects.filter(role=CustomUser.Role.TEACHER, is_active=True)
        .annotate(
            avg_stars=Avg('received_teacher_ratings__stars'),
            rating_count=Count('received_teacher_ratings'),
        )
        .order_by('-avg_stars', '-rating_count', 'first_name')
    )
    return render(request, 'core/teacher_ratings.html', {
        'teachers': teachers,
    })


@login_required
@require_POST
def rate_teacher(request, teacher_id):
    teacher = get_object_or_404(
        CustomUser, pk=teacher_id, role=CustomUser.Role.TEACHER, is_active=True
    )
    try:
        stars = int(request.POST.get('stars', 0))
    except (TypeError, ValueError):
        stars = 0
    if stars < 1 or stars > 5:
        messages.error(request, 'Baholash 1 dan 5 gacha bo‘lishi kerak.')
        return redirect(request.META.get('HTTP_REFERER') or 'core:teacher_rating_list')

    lesson_id = request.POST.get('lesson_id') or None
    if lesson_id in ('', 'None'):
        lesson_id = None
    comment = (request.POST.get('comment') or '').strip()[:300]
    defaults = {'stars': stars, 'comment': comment}
    if lesson_id:
        TeacherRating.objects.update_or_create(
            student=request.user,
            teacher=teacher,
            lesson_id=lesson_id,
            defaults=defaults,
        )
    else:
        obj = TeacherRating.objects.filter(
            student=request.user, teacher=teacher, lesson__isnull=True
        ).first()
        if obj:
            obj.stars = stars
            obj.comment = comment
            obj.save(update_fields=['stars', 'comment', 'updated_at'])
        else:
            TeacherRating.objects.create(
                student=request.user,
                teacher=teacher,
                lesson=None,
                stars=stars,
                comment=comment,
            )
    messages.success(request, 'Bahongiz saqlandi. Rahmat!')
    return redirect(request.META.get('HTTP_REFERER') or 'core:teacher_rating_list')


def founder_detail(request, pk):
    founder = get_object_or_404(Founder, pk=pk, is_active=True)
    return render(request, 'core/person_detail.html', {
        'person_kind': 'founder',
        'person': founder,
        'back_anchor': 'asoschilar',
    })


def teacher_detail(request, pk):
    # show_on_homepage faqat landing uchun — batafsil sahifa barcha faol o‘qituvchiga ochiq
    teacher = get_object_or_404(
        CustomUser,
        pk=pk,
        role=CustomUser.Role.TEACHER,
        is_active=True,
    )
    stats = TeacherRating.objects.filter(teacher=teacher).aggregate(
        avg=Avg('stars'), count=Count('id')
    )
    return render(request, 'core/person_detail.html', {
        'person_kind': 'teacher',
        'person': teacher,
        'back_anchor': 'oqituvchilar',
        'teacher_avg': stats['avg'],
        'teacher_rating_count': stats['count'] or 0,
    })


@login_required
def notifications_list(request):
    """Foydalanuvchining barcha bildirishnomalari — ochilganda hammasi o‘qilgan deb belgilanadi."""
    from .models import Notification

    qs = Notification.objects.filter(user=request.user)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': qs})


@login_required
@require_POST
def notification_read(request, pk):
    """Bitta bildirishnomani o‘qilgan deb belgilaydi va havolasi bo‘lsa o‘sha yerga o‘tkazadi."""
    from .models import Notification

    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=['is_read', 'updated_at'])
    return redirect(notif.url or 'core:notifications')


def about(request):
    """Platforma haqida qisqa va to‘liq ma’lumot."""
    return render(request, 'core/about.html', {})


def error_404(request, exception=None):
    logger.info('404 Not Found: %s', request.path)
    return render(request, 'errors/404.html', status=404)


def error_403(request, exception=None):
    logger.warning('403 Forbidden: %s (user=%s)', request.path, getattr(request.user, 'username', 'anonymous'))
    return render(request, 'errors/403.html', status=403)


def error_500(request):
    logger.error('500 Server Error: %s', request.path)
    return render(request, 'errors/500.html', status=500)
