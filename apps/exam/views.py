"""Exam views — per-lesson 10-question tests."""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.education.models import Lesson
from apps.subscription.access import can_access_exam_for_lesson, can_start_lesson_exam

from .constants import QUESTIONS_PER_LESSON
from .models import Answer, ExamAttempt, Question
from .services import (
    build_session_payload,
    calculate_result,
    get_exam_settings_for_lesson,
    lesson_question_bank_ready,
    save_attempt,
    select_questions_for_lesson,
)

SESSION_KEY_TEMPLATE = 'exam_session_lesson_{}'


def _session_still_valid(session_data, time_limit_minutes):
    """Return (ok, seconds_left). Server enforces time limit."""
    started_at = parse_datetime(session_data.get('started_at', '')) or timezone.now()
    if timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at)
    if not time_limit_minutes:
        return True, None
    expires_at = started_at + timedelta(minutes=time_limit_minutes)
    # 15s grace for network/submit lag
    seconds_left = int((expires_at - timezone.now()).total_seconds()) + 15
    return seconds_left > 0, max(0, int((expires_at - timezone.now()).total_seconds()))


@login_required
def exam_start(request, lesson_pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related('topic'),
        pk=lesson_pk,
        is_active=True,
    )

    if not can_access_exam_for_lesson(request.user, lesson):
        messages.warning(
            request,
            f"«{lesson.title}» testi pullik. Faol obuna kerak — Obuna sahifasidan so‘rov yuboring.",
        )
        return redirect('subscription:info')

    if not can_start_lesson_exam(request.user, lesson):
        messages.warning(request, "Testni boshlash uchun avval shu video darsni tugating.")
        return redirect('education:lesson_detail', pk=lesson_pk)

    ready, valid_count = lesson_question_bank_ready(lesson)
    settings_info = get_exam_settings_for_lesson(lesson)
    session_key = SESSION_KEY_TEMPLATE.format(lesson_pk)
    existing_session = request.session.get(session_key)
    can_resume = False
    if existing_session:
        ok, _ = _session_still_valid(existing_session, settings_info['time_limit_minutes'])
        can_resume = ok
        if not ok:
            del request.session[session_key]
            existing_session = None

    if request.method == 'POST':
        action = request.POST.get('action', 'start')
        if action == 'resume' and can_resume:
            return redirect('exam:exam_take', lesson_pk=lesson_pk)

        if action == 'restart' and existing_session:
            del request.session[session_key]

        if not ready:
            messages.error(
                request,
                f"Bu video uchun hali {QUESTIONS_PER_LESSON} ta to‘liq savol yo‘q "
                f"(hozir: {valid_count}).",
            )
            return redirect('education:lesson_detail', pk=lesson_pk)

        questions = select_questions_for_lesson(request.user, lesson)
        if not questions:
            messages.error(request, "Test savollari tayyor emas.")
            return redirect('education:lesson_detail', pk=lesson_pk)

        payload = build_session_payload(questions)
        request.session[session_key] = {
            'payload': payload,
            'started_at': timezone.now().isoformat(),
        }
        return redirect('exam:exam_take', lesson_pk=lesson_pk)

    return render(request, 'exam/exam_start.html', {
        'lesson': lesson,
        'topic': lesson.topic,
        'settings': settings_info,
        'bank_ready': ready,
        'valid_count': valid_count,
        'required_count': QUESTIONS_PER_LESSON,
        'can_resume': can_resume,
    })


@login_required
def exam_take(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk, is_active=True)
    session_key = SESSION_KEY_TEMPLATE.format(lesson_pk)
    session_data = request.session.get(session_key)
    if not session_data:
        return redirect('exam:exam_start', lesson_pk=lesson_pk)

    settings_info = get_exam_settings_for_lesson(lesson)
    ok, seconds_left = _session_still_valid(session_data, settings_info['time_limit_minutes'])
    if not ok:
        # Auto-submit empty remaining answers when time is up
        messages.warning(request, 'Vaqt tugadi — javoblaringiz qabul qilindi.')
        return _finalize_submit(request, lesson, session_key, session_data, auto=True)

    payload = session_data['payload']
    question_ids = [entry['question_id'] for entry in payload]
    questions_by_id = {
        q.id: q for q in Question.objects.filter(id__in=question_ids).prefetch_related('answers')
    }

    items = []
    for entry in payload:
        answer_ids = entry['answer_order']
        answers_by_id = {a.id: a for a in Answer.objects.filter(id__in=answer_ids)}
        ordered_answers = [answers_by_id[aid] for aid in answer_ids if aid in answers_by_id]
        items.append({
            'question': questions_by_id[entry['question_id']],
            'answers': ordered_answers,
        })

    return render(request, 'exam/exam_take.html', {
        'lesson': lesson,
        'topic': lesson.topic,
        'items': items,
        'time_limit': settings_info['time_limit_minutes'],
        'seconds_left': seconds_left,
    })


def _finalize_submit(request, lesson, session_key, session_data, auto=False):
    payload = session_data['payload']
    submitted_answers = {
        key[len('question_'):]: value
        for key, value in request.POST.items()
        if key.startswith('question_')
    }

    summary, attempt_question_rows = calculate_result(payload, submitted_answers, lesson)

    started_at = parse_datetime(session_data['started_at']) or timezone.now()
    if timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at)
    duration_seconds = int((timezone.now() - started_at).total_seconds())

    attempt = save_attempt(request.user, lesson, summary, attempt_question_rows, duration_seconds)
    if session_key in request.session:
        del request.session[session_key]
    return redirect('exam:exam_result', pk=attempt.pk)


@login_required
def exam_submit(request, lesson_pk):
    if request.method != 'POST':
        return redirect('exam:exam_start', lesson_pk=lesson_pk)

    lesson = get_object_or_404(Lesson, pk=lesson_pk, is_active=True)
    session_key = SESSION_KEY_TEMPLATE.format(lesson_pk)
    session_data = request.session.get(session_key)
    if not session_data:
        messages.error(request, 'Test sessiyasi tugagan. Qaytadan boshlang.')
        return redirect('exam:exam_start', lesson_pk=lesson_pk)

    settings_info = get_exam_settings_for_lesson(lesson)
    ok, _ = _session_still_valid(session_data, settings_info['time_limit_minutes'])
    # Even if time expired, accept submit (timer auto-submit / late network)
    if not ok:
        messages.info(request, 'Vaqt tugagan edi — yakuniy javoblar saqlandi.')

    return _finalize_submit(request, lesson, session_key, session_data)


@login_required
def exam_result(request, pk):
    attempt = get_object_or_404(
        ExamAttempt.objects.select_related('topic', 'lesson'),
        pk=pk,
        user=request.user,
    )
    attempt_questions = attempt.attempt_questions.select_related(
        'question', 'selected_answer'
    ).prefetch_related('question__answers')

    return render(request, 'exam/exam_result.html', {
        'attempt': attempt,
        'attempt_questions': attempt_questions,
    })


@login_required
def exam_history(request, lesson_pk):
    lesson = get_object_or_404(Lesson.objects.select_related('topic'), pk=lesson_pk, is_active=True)
    attempts = ExamAttempt.objects.filter(user=request.user, lesson=lesson)
    best_attempt = attempts.order_by('-score').first()

    return render(request, 'exam/exam_history.html', {
        'lesson': lesson,
        'topic': lesson.topic,
        'attempts': attempts,
        'best_attempt': best_attempt,
    })
