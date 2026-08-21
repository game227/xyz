"""Progress chart context tests."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.models import ExamAttempt
from apps.progress.models import LessonProgress
from apps.progress.services import get_dashboard_context
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class ProgressChartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='chart_user', email='c@xyz.uz', password='pass12345'
        )
        subject = Subject.objects.create(name='Matematika', is_active=True)
        course = Course.objects.create(subject=subject, title='Algebra', order=1, is_active=True)
        module = Module.objects.create(course=course, title='M1', order=1, is_active=True)
        topic = Topic.objects.create(module=module, title='T1', order=1, is_active=True)
        video = SimpleUploadedFile('a.mp4', b'fake', content_type='video/mp4')
        self.lesson = Lesson.objects.create(
            topic=topic, title='Dars 1', order=1, is_active=True,
            duration_minutes=5, video=video,
        )

    def test_empty_chart_flags(self):
        ctx = get_dashboard_context(self.user)
        self.assertEqual(ctx['progress_chart'], [])
        self.assertEqual(len(ctx['weekly_chart']), 8)
        self.assertFalse(ctx['has_chart_data'])

    def test_chart_fills_after_attempt(self):
        ExamAttempt.objects.create(
            user=self.user,
            topic=self.lesson.topic,
            lesson=self.lesson,
            score=80,
            correct_answers=8,
            wrong_answers=2,
            total_questions=10,
            is_passed=True,
            duration_seconds=120,
        )
        LessonProgress.objects.create(
            user=self.user,
            lesson=self.lesson,
            is_completed=True,
            watch_percent=100,
            completed_at=timezone.now(),
        )
        ctx = get_dashboard_context(self.user)
        self.assertTrue(ctx['has_chart_data'])
        self.assertTrue(len(ctx['progress_chart']) >= 1)
        self.assertEqual(ctx['progress_chart'][-1]['avg_score'], 80.0)
        self.assertTrue(any(p['attempts'] >= 1 for p in ctx['weekly_chart']))
        self.assertTrue(any(p['lessons_completed'] >= 1 for p in ctx['weekly_chart']))
