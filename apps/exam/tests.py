"""Exam engine tests — question bank rules, selection, and scoring."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.education.models import Course, Lesson, Module, Subject, Topic

from .constants import QUESTIONS_PER_LESSON
from .models import Answer, ExamSettings, Question
from .services import calculate_result, select_questions_for_lesson


def make_lesson():
    subject = Subject.objects.create(name='Fan')
    course = Course.objects.create(subject=subject, title='Kurs', order=1)
    module = Module.objects.create(course=course, title='Modul', order=1)
    topic = Topic.objects.create(module=module, title='Mavzu', order=1)
    video = SimpleUploadedFile('v.mp4', b'fake', content_type='video/mp4')
    return Lesson.objects.create(
        topic=topic, title='Dars', order=1, duration_minutes=5, video=video,
    )


def add_question_with_answers(lesson, correct_index=0, answer_count=4, active=True):
    question = Question.objects.create(
        lesson=lesson, topic=lesson.topic, text='Savol', is_active=active,
    )
    for i in range(answer_count):
        Answer.objects.create(
            question=question, text=f'Javob {i}', is_correct=(i == correct_index), order=i,
        )
    return question


class QuestionBankLimitTests(TestCase):
    def setUp(self):
        self.lesson = make_lesson()

    def test_allows_up_to_ten_active_questions(self):
        for _ in range(QUESTIONS_PER_LESSON):
            q = Question(lesson=self.lesson, text='Savol', is_active=True)
            q.clean()
            q.save()
        self.assertEqual(
            Question.objects.filter(lesson=self.lesson, is_active=True).count(),
            QUESTIONS_PER_LESSON,
        )

    def test_eleventh_active_question_rejected(self):
        for _ in range(QUESTIONS_PER_LESSON):
            Question.objects.create(lesson=self.lesson, text='Savol', is_active=True)
        eleventh = Question(lesson=self.lesson, text='11-savol', is_active=True)
        with self.assertRaises(ValidationError):
            eleventh.clean()

    def test_inactive_question_does_not_count_toward_limit(self):
        for _ in range(QUESTIONS_PER_LESSON):
            Question.objects.create(lesson=self.lesson, text='Savol', is_active=True)
        inactive = Question(lesson=self.lesson, text='Zaxira savol', is_active=False)
        inactive.clean()  # should not raise — inactive doesn't count


class HasValidAnswersTests(TestCase):
    def setUp(self):
        self.lesson = make_lesson()

    def test_question_with_four_answers_one_correct_is_valid(self):
        q = add_question_with_answers(self.lesson)
        self.assertTrue(q.has_valid_answers)

    def test_question_with_too_few_answers_is_invalid(self):
        q = Question.objects.create(lesson=self.lesson, text='Savol', is_active=True)
        Answer.objects.create(question=q, text='Yagona', is_correct=True, order=0)
        self.assertFalse(q.has_valid_answers)

    def test_question_with_two_correct_answers_is_invalid(self):
        q = Question.objects.create(lesson=self.lesson, text='Savol', is_active=True)
        for i in range(4):
            Answer.objects.create(question=q, text=f'J{i}', is_correct=(i < 2), order=i)
        self.assertFalse(q.has_valid_answers)


class SelectQuestionsForLessonTests(TestCase):
    def setUp(self):
        self.lesson = make_lesson()

    def test_returns_empty_when_not_enough_valid_questions(self):
        for _ in range(QUESTIONS_PER_LESSON - 1):
            add_question_with_answers(self.lesson)
        self.assertEqual(select_questions_for_lesson(None, self.lesson), [])

    def test_returns_exactly_ten_when_bank_is_ready(self):
        for _ in range(QUESTIONS_PER_LESSON):
            add_question_with_answers(self.lesson)
        selected = select_questions_for_lesson(None, self.lesson)
        self.assertEqual(len(selected), QUESTIONS_PER_LESSON)

    def test_invalid_questions_excluded_from_selection(self):
        for _ in range(QUESTIONS_PER_LESSON):
            add_question_with_answers(self.lesson)
        # Add a broken question (no correct answer) — should never be selected.
        broken = Question.objects.create(lesson=self.lesson, text='Buzuq', is_active=True)
        Answer.objects.create(question=broken, text='J', is_correct=False, order=0)

        selected = select_questions_for_lesson(None, self.lesson)
        self.assertNotIn(broken, selected)


class CalculateResultTests(TestCase):
    def setUp(self):
        self.lesson = make_lesson()
        ExamSettings.objects.create(topic=self.lesson.topic, passing_score=70)
        self.questions = [add_question_with_answers(self.lesson) for _ in range(QUESTIONS_PER_LESSON)]
        self.session_payload = [{'question_id': q.id} for q in self.questions]

    def test_all_correct_gives_100_percent_and_pass(self):
        submitted = {
            str(q.id): str(q.answers.get(is_correct=True).id) for q in self.questions
        }
        summary, rows = calculate_result(self.session_payload, submitted, self.lesson)
        self.assertEqual(summary['correct_answers'], QUESTIONS_PER_LESSON)
        self.assertEqual(summary['wrong_answers'], 0)
        self.assertEqual(summary['score'], Decimal('100.00'))
        self.assertTrue(summary['is_passed'])

    def test_below_passing_score_fails(self):
        # Answer only 2 correctly (20%) — below the 70% passing score.
        submitted = {}
        for i, q in enumerate(self.questions):
            correct = q.answers.get(is_correct=True)
            wrong = q.answers.exclude(is_correct=True).first()
            submitted[str(q.id)] = str(correct.id if i < 2 else wrong.id)

        summary, rows = calculate_result(self.session_payload, submitted, self.lesson)
        self.assertEqual(summary['correct_answers'], 2)
        self.assertEqual(summary['score'], Decimal('20.00'))
        self.assertFalse(summary['is_passed'])

    def test_missing_answer_counts_as_wrong(self):
        submitted = {}  # nothing answered
        summary, rows = calculate_result(self.session_payload, submitted, self.lesson)
        self.assertEqual(summary['correct_answers'], 0)
        self.assertEqual(summary['wrong_answers'], QUESTIONS_PER_LESSON)
        self.assertEqual(len(rows), QUESTIONS_PER_LESSON)
        self.assertTrue(all(row['selected_answer_id'] is None for row in rows))
