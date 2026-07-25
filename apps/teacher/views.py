"""Teacher portal — full content CRUD focused on lessons + 10-q banks."""
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.constants import QUESTIONS_PER_LESSON
from apps.exam.models import ExamAttempt, ExamSettings, Question
from apps.exam.services import lesson_question_bank_ready

from .decorators import teacher_required
from .forms import (
    AnswerFormSet,
    CourseForm,
    ExamSettingsForm,
    LessonForm,
    ModuleForm,
    QuestionForm,
    SubjectForm,
    TopicForm,
)


@teacher_required
def dashboard(request):
    stats = {
        'subjects': Subject.objects.count(),
        'lessons': Lesson.objects.count(),
        'questions': Question.objects.count(),
        'attempts': ExamAttempt.objects.count(),
    }
    recent_lessons = (
        Lesson.objects.select_related('topic')
        .annotate(q_count=Count('questions'))
        .order_by('-created_at')[:8]
    )
    return render(request, 'teacher/dashboard.html', {
        'stats': stats,
        'recent_lessons': recent_lessons,
        'questions_per_lesson': QUESTIONS_PER_LESSON,
    })


# ---- Curriculum CRUD ----

@teacher_required
def subject_list(request):
    subjects = Subject.objects.annotate(course_count=Count('courses')).order_by('name')
    return render(request, 'teacher/subject_list.html', {'subjects': subjects})


@teacher_required
def subject_create(request):
    form = SubjectForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fan yaratildi.')
        return redirect('teacher:subject_list')
    return render(request, 'teacher/simple_form.html', {'form': form, 'title': 'Yangi fan'})


@teacher_required
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, request.FILES or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fan yangilandi.')
        return redirect('teacher:subject_list')
    return render(request, 'teacher/simple_form.html', {'form': form, 'title': 'Fanni tahrirlash'})


@teacher_required
@require_POST
def subject_delete(request, pk):
    get_object_or_404(Subject, pk=pk).delete()
    messages.success(request, 'Fan o‘chirildi.')
    return redirect('teacher:subject_list')


@teacher_required
def course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kurs yaratildi.')
        return redirect('teacher:subject_list')
    return render(request, 'teacher/simple_form.html', {'form': form, 'title': 'Yangi kurs'})


@teacher_required
def module_create(request):
    form = ModuleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Modul yaratildi.')
        return redirect('teacher:topic_list')
    return render(request, 'teacher/simple_form.html', {'form': form, 'title': 'Yangi modul'})


@teacher_required
def topic_list(request):
    topics = (
        Topic.objects.select_related('module', 'module__course', 'module__course__subject')
        .annotate(
            lesson_count=Count('lessons', distinct=True),
            question_count=Count('questions', distinct=True),
        )
        .order_by('module__course__subject__name', 'module__course__order', 'module__order', 'order')
    )
    return render(request, 'teacher/topic_list.html', {'topics': topics})


@teacher_required
def topic_create(request):
    form = TopicForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        topic = form.save()
        ExamSettings.objects.get_or_create(topic=topic)
        messages.success(request, 'Mavzu yaratildi.')
        return redirect('teacher:topic_detail', pk=topic.pk)
    return render(request, 'teacher/simple_form.html', {'form': form, 'title': 'Yangi mavzu'})


@teacher_required
def topic_detail(request, pk):
    topic = get_object_or_404(
        Topic.objects.select_related('module', 'module__course', 'module__course__subject'),
        pk=pk,
    )
    lessons = topic.lessons.annotate(q_count=Count('questions')).order_by('order', 'id')
    settings_obj, _ = ExamSettings.objects.get_or_create(topic=topic)
    lesson_rows = []
    for lesson in lessons:
        ready, valid = lesson_question_bank_ready(lesson)
        lesson_rows.append({
            'lesson': lesson,
            'q_count': lesson.q_count,
            'valid_count': valid,
            'ready': ready,
        })
    return render(request, 'teacher/topic_detail.html', {
        'topic': topic,
        'lesson_rows': lesson_rows,
        'settings': settings_obj,
        'questions_per_lesson': QUESTIONS_PER_LESSON,
    })


@teacher_required
def exam_settings_edit(request, topic_pk):
    topic = get_object_or_404(Topic, pk=topic_pk)
    settings_obj, _ = ExamSettings.objects.get_or_create(topic=topic)
    form = ExamSettingsForm(request.POST or None, instance=settings_obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Test sozlamalari saqlandi (har video = 10 savol).')
        return redirect('teacher:topic_detail', pk=topic.pk)
    return render(request, 'teacher/exam_settings_form.html', {
        'form': form,
        'topic': topic,
        'questions_per_lesson': QUESTIONS_PER_LESSON,
    })


# ---- Lessons CRUD ----

@teacher_required
def lesson_list(request):
    lessons = (
        Lesson.objects.select_related('topic', 'topic__module__course__subject')
        .annotate(q_count=Count('questions'))
        .order_by('-created_at')
    )
    return render(request, 'teacher/lesson_list.html', {
        'lessons': lessons,
        'questions_per_lesson': QUESTIONS_PER_LESSON,
    })


@teacher_required
def lesson_create(request, topic_pk=None):
    topic = get_object_or_404(Topic, pk=topic_pk) if topic_pk else None
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, topic_fixed=topic)
        if form.is_valid():
            lesson = form.save(commit=False)
            if topic:
                lesson.topic = topic
            lesson.created_by = request.user
            lesson.save()
            messages.success(request, 'Video dars qo‘shildi. Endi 10 ta savol qo‘shing.')
            return redirect('teacher:lesson_detail', pk=lesson.pk)
    else:
        initial = {'is_active': True}
        if topic:
            initial['order'] = (topic.lessons.count() or 0) + 1
        form = LessonForm(initial=initial, topic_fixed=topic)
    return render(request, 'teacher/lesson_form.html', {
        'form': form,
        'topic': topic,
        'title': 'Yangi video dars',
    })


@teacher_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related('topic', 'topic__module__course__subject'),
        pk=pk,
    )
    questions = lesson.questions.prefetch_related('answers').order_by('id')
    ready, valid = lesson_question_bank_ready(lesson)
    return render(request, 'teacher/lesson_detail.html', {
        'lesson': lesson,
        'questions': questions,
        'ready': ready,
        'valid_count': valid,
        'questions_per_lesson': QUESTIONS_PER_LESSON,
    })


@teacher_required
def lesson_edit(request, pk):
    lesson = get_object_or_404(Lesson.objects.select_related('topic'), pk=pk)
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'Video dars yangilandi.')
            return redirect('teacher:lesson_detail', pk=lesson.pk)
    else:
        form = LessonForm(instance=lesson)
    return render(request, 'teacher/lesson_form.html', {
        'form': form,
        'topic': lesson.topic,
        'title': 'Darsni tahrirlash',
        'lesson': lesson,
    })


@teacher_required
@require_POST
def lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    topic_id = lesson.topic_id
    lesson.delete()
    messages.success(request, 'Video dars o‘chirildi.')
    return redirect('teacher:topic_detail', pk=topic_id)


# ---- Questions (bound to lesson) ----

@teacher_required
def question_create(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST, lesson=lesson)
        formset = AnswerFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.lesson = lesson
            question.topic = lesson.topic
            question.created_by = request.user
            question.save()
            formset.instance = question
            formset.save()
            messages.success(request, 'Savol qo‘shildi.')
            return redirect('teacher:lesson_detail', pk=lesson.pk)
    else:
        form = QuestionForm(initial={'is_active': True}, lesson=lesson)
        formset = AnswerFormSet()
    return render(request, 'teacher/question_form.html', {
        'form': form,
        'formset': formset,
        'lesson': lesson,
        'title': 'Yangi savol',
    })


@teacher_required
def question_edit(request, pk):
    question = get_object_or_404(Question.objects.select_related('lesson', 'topic'), pk=pk)
    lesson = question.lesson
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question, lesson=lesson)
        formset = AnswerFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Savol yangilandi.')
            return redirect('teacher:lesson_detail', pk=lesson.pk)
    else:
        form = QuestionForm(instance=question, lesson=lesson)
        formset = AnswerFormSet(instance=question)
    return render(request, 'teacher/question_form.html', {
        'form': form,
        'formset': formset,
        'lesson': lesson,
        'title': 'Savolni tahrirlash',
        'question': question,
    })


@teacher_required
@require_POST
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk)
    lesson_id = question.lesson_id
    question.delete()
    messages.success(request, 'Savol o‘chirildi.')
    return redirect('teacher:lesson_detail', pk=lesson_id)
