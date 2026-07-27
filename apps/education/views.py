"""Education views — curriculum browsing + per-lesson test CTA."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.exam.models import ExamAttempt
from apps.subscription.access import (
    can_access_lesson,
    can_start_lesson_exam,
    get_freemium_lesson,
    is_freemium_lesson,
)
from apps.subscription.services import has_active_subscription

from .models import Course, Lesson, Module, Subject, Topic


@login_required
def subject_list(request):
    subjects = Subject.objects.filter(is_active=True)
    free_lesson = get_freemium_lesson()
    return render(request, 'education/subject_list.html', {
        'subjects': subjects,
        'free_lesson': free_lesson,
        'has_subscription': has_active_subscription(request.user),
    })


@login_required
def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk, is_active=True)
    courses = subject.courses.filter(is_active=True)
    return render(request, 'education/subject_detail.html', {
        'subject': subject,
        'courses': courses,
        'has_subscription': has_active_subscription(request.user),
        'free_lesson': get_freemium_lesson(),
    })


@login_required
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related('subject'), pk=pk, is_active=True
    )
    modules = course.modules.filter(is_active=True)
    return render(request, 'education/course_detail.html', {
        'course': course,
        'modules': modules,
        'has_subscription': has_active_subscription(request.user),
        'free_lesson': get_freemium_lesson(),
    })


@login_required
def module_detail(request, pk):
    module = get_object_or_404(
        Module.objects.select_related('course', 'course__subject'), pk=pk, is_active=True
    )
    topics = module.topics.filter(is_active=True)
    free = get_freemium_lesson()
    return render(request, 'education/module_detail.html', {
        'module': module,
        'topics': topics,
        'has_subscription': has_active_subscription(request.user),
        'free_topic': free.topic if free else None,
    })


@login_required
def topic_detail(request, pk):
    topic = get_object_or_404(
        Topic.objects.select_related('module', 'module__course', 'module__course__subject'),
        pk=pk, is_active=True,
    )
    lessons = list(topic.lessons.filter(is_active=True))
    completed_lesson_ids = set(
        request.user.lesson_progress.filter(is_completed=True).values_list('lesson_id', flat=True)
    )
    passed_exam_ids = set(
        ExamAttempt.objects.filter(
            user=request.user, lesson__in=lessons, is_passed=True
        ).values_list('lesson_id', flat=True)
    )
    free_lesson = get_freemium_lesson()
    lesson_items = [
        {
            'lesson': lesson,
            'accessible': can_access_lesson(request.user, lesson),
            'completed': lesson.id in completed_lesson_ids,
            'exam_passed': lesson.id in passed_exam_ids,
            'can_start_test': can_start_lesson_exam(request.user, lesson),
            'is_free': free_lesson and lesson.id == free_lesson.id,
        }
        for lesson in lessons
    ]

    return render(request, 'education/topic_detail.html', {
        'topic': topic,
        'lesson_items': lesson_items,
        'has_subscription': has_active_subscription(request.user),
        'free_lesson': free_lesson,
    })


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related(
            'topic', 'topic__module', 'topic__module__course', 'topic__module__course__subject'
        ),
        pk=pk,
        is_active=True,
    )

    if not can_access_lesson(request.user, lesson):
        messages.warning(
            request,
            f"«{lesson.title}» — pullik dars. Katalog ochiq, lekin tomosha uchun "
            "faol obuna kerak. Obuna sahifasidan so‘rov yuboring.",
        )
        return redirect('subscription:info')

    all_lessons = list(lesson.topic.lessons.filter(is_active=True))
    next_lesson = next((item for item in all_lessons if item.order > lesson.order), None)
    if next_lesson and not can_access_lesson(request.user, next_lesson):
        next_lesson = None

    progress = request.user.lesson_progress.filter(lesson=lesson).first()
    is_completed = bool(progress and progress.is_completed)
    watch_percent = progress.watch_percent if progress else 0
    from apps.subscription.access import MIN_WATCH_PERCENT_TO_COMPLETE
    can_mark_complete = watch_percent >= MIN_WATCH_PERCENT_TO_COMPLETE or is_completed
    can_start_test = can_start_lesson_exam(request.user, lesson)
    best_attempt = (
        ExamAttempt.objects.filter(user=request.user, lesson=lesson)
        .order_by('-score')
        .first()
    )

    return render(request, 'education/lesson_detail.html', {
        'lesson': lesson,
        'next_lesson': next_lesson,
        'is_completed': is_completed,
        'is_free': is_freemium_lesson(lesson),
        'has_subscription': has_active_subscription(request.user),
        'can_start_test': can_start_test,
        'best_attempt': best_attempt,
        'watch_percent': watch_percent,
        'min_watch_percent': MIN_WATCH_PERCENT_TO_COMPLETE,
        'can_mark_complete': can_mark_complete,
    })
