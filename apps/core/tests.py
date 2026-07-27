"""Integration tests for XYZ freemium + per-lesson 10-question exams."""
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.constants import QUESTIONS_PER_LESSON
from apps.exam.models import Answer, ExamSettings, Question
from apps.progress.models import LessonProgress
from apps.subscription.access import (
    can_access_exam_for_lesson,
    can_access_lesson,
    get_freemium_lesson,
)
from apps.subscription.services import activate_subscription


def add_ten_questions(lesson):
    for i in range(QUESTIONS_PER_LESSON):
        q = Question.objects.create(
            lesson=lesson, topic=lesson.topic, text=f'{lesson.id} Savol {i}', is_active=True
        )
        for j in range(4):
            Answer.objects.create(
                question=q, text=f'Javob {j}', is_correct=(j == 0), order=j + 1
            )


class SettingsTests(TestCase):
    def test_sqlite_fallback_is_enabled_by_default(self):
        self.assertTrue(settings.DATABASES['default']['ENGINE'].endswith('sqlite3'))


class FreemiumFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_superuser(
            username='admin', email='a@xyz.uz', password='admin12345'
        )
        self.student = CustomUser.objects.create_user(
            username='student', email='s@xyz.uz', password='student12345'
        )
        subject = Subject.objects.create(name='Matematika', is_active=True)
        course = Course.objects.create(subject=subject, title='Algebra', order=1, is_active=True)
        module = Module.objects.create(course=course, title='Modul 1', order=1, is_active=True)
        self.topic = Topic.objects.create(module=module, title='Mavzu 1', order=1, is_active=True)
        self.topic2 = Topic.objects.create(module=module, title='Mavzu 2', order=2, is_active=True)

        video = SimpleUploadedFile('a.mp4', b'fake-video-bytes', content_type='video/mp4')
        self.free_lesson = Lesson.objects.create(
            topic=self.topic, title='Free lesson', order=1, is_active=True,
            duration_minutes=5, video=video,
        )
        video2 = SimpleUploadedFile('b.mp4', b'fake-video-bytes-2', content_type='video/mp4')
        self.paid_lesson = Lesson.objects.create(
            topic=self.topic, title='Paid lesson', order=2, is_active=True,
            duration_minutes=5, video=video2,
        )
        video3 = SimpleUploadedFile('c.mp4', b'fake-video-bytes-3', content_type='video/mp4')
        self.other_topic_lesson = Lesson.objects.create(
            topic=self.topic2, title='Other topic lesson', order=1, is_active=True,
            duration_minutes=5, video=video3,
        )

        ExamSettings.objects.create(topic=self.topic, question_count=10, passing_score=50)
        add_ten_questions(self.free_lesson)
        add_ten_questions(self.paid_lesson)

    def test_freemium_lesson_detection(self):
        self.assertEqual(get_freemium_lesson().id, self.free_lesson.id)
        self.assertTrue(can_access_lesson(self.student, self.free_lesson))
        self.assertFalse(can_access_lesson(self.student, self.paid_lesson))
        self.assertTrue(can_access_exam_for_lesson(self.student, self.free_lesson))
        self.assertFalse(can_access_exam_for_lesson(self.student, self.paid_lesson))

    def test_student_can_open_free_lesson_but_not_paid(self):
        self.client.login(username='student', password='student12345')
        free = self.client.get(reverse('education:lesson_detail', args=[self.free_lesson.pk]))
        self.assertEqual(free.status_code, 200)

        paid = self.client.get(reverse('education:lesson_detail', args=[self.paid_lesson.pk]))
        self.assertEqual(paid.status_code, 302)
        self.assertIn('/subscription/', paid.url)

    def test_free_exam_after_completing_free_lesson_and_saves_result(self):
        self.client.login(username='student', password='student12345')
        LessonProgress.objects.create(
            user=self.student, lesson=self.free_lesson, watch_percent=80
        )
        self.client.post(reverse('progress:mark_lesson_complete', args=[self.free_lesson.pk]))
        self.assertTrue(
            LessonProgress.objects.filter(
                user=self.student, lesson=self.free_lesson, is_completed=True
            ).exists()
        )

        start = self.client.post(reverse('exam:exam_start', args=[self.free_lesson.pk]))
        self.assertEqual(start.status_code, 302)
        take = self.client.get(reverse('exam:exam_take', args=[self.free_lesson.pk]))
        self.assertEqual(take.status_code, 200)
        self.assertEqual(len(take.context['items']), QUESTIONS_PER_LESSON)

        session = self.client.session[f'exam_session_lesson_{self.free_lesson.pk}']
        payload = session['payload']
        self.assertEqual(len(payload), QUESTIONS_PER_LESSON)
        post_data = {}
        for entry in payload:
            qid = entry['question_id']
            correct = Answer.objects.get(question_id=qid, is_correct=True)
            post_data[f'question_{qid}'] = str(correct.id)

        submit = self.client.post(reverse('exam:exam_submit', args=[self.free_lesson.pk]), post_data)
        self.assertEqual(submit.status_code, 302)
        self.assertTrue(self.student.exam_attempts.filter(lesson=self.free_lesson).exists())

    def test_subscription_unlocks_paid_lesson(self):
        activate_subscription(self.student, 30, self.admin)
        self.client.login(username='student', password='student12345')
        paid = self.client.get(reverse('education:lesson_detail', args=[self.paid_lesson.pk]))
        self.assertEqual(paid.status_code, 200)

    def test_home_page_branded_xyz(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'XYZ')
