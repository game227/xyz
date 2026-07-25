from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.constants import QUESTIONS_PER_LESSON
from apps.exam.models import Answer, Question

User = get_user_model()


class TeacherPanelTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='t1', password='pass12345', role=User.Role.TEACHER
        )
        self.student = User.objects.create_user(
            username='s1', password='pass12345', role=User.Role.STUDENT
        )
        subject = Subject.objects.create(name='Matematika')
        course = Course.objects.create(subject=subject, title='Algebra', order=1)
        module = Module.objects.create(course=course, title='Modul 1', order=1)
        self.topic = Topic.objects.create(module=module, title='Mavzu 1', order=1)

    def test_student_blocked_from_teacher(self):
        self.client.login(username='s1', password='pass12345')
        response = self.client.get(reverse('teacher:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_teacher_can_create_lesson_and_questions(self):
        self.client.login(username='t1', password='pass12345')
        dash = self.client.get(reverse('teacher:dashboard'))
        self.assertEqual(dash.status_code, 200)

        video = SimpleUploadedFile('demo.mp4', b'fake-video', content_type='video/mp4')
        response = self.client.post(
            reverse('teacher:lesson_create_for_topic', args=[self.topic.pk]),
            {
                'title': 'Yangi dars',
                'description': 'Test',
                'video': video,
                'duration_minutes': 10,
                'order': 1,
                'is_active': True,
            },
        )
        self.assertEqual(response.status_code, 302)
        lesson = Lesson.objects.get(title='Yangi dars')
        self.assertEqual(lesson.created_by_id, self.teacher.id)

        detail = self.client.get(reverse('teacher:lesson_detail', args=[lesson.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, f'{QUESTIONS_PER_LESSON}')

        # Add one question
        response = self.client.post(
            reverse('teacher:question_create', args=[lesson.pk]),
            {
                'text': '2+2=?',
                'explanation': '',
                'difficulty': 'EASY',
                'is_active': True,
                'answers-TOTAL_FORMS': '4',
                'answers-INITIAL_FORMS': '0',
                'answers-MIN_NUM_FORMS': '0',
                'answers-MAX_NUM_FORMS': '1000',
                'answers-0-text': '4',
                'answers-0-is_correct': 'on',
                'answers-0-order': '1',
                'answers-1-text': '3',
                'answers-1-order': '2',
                'answers-2-text': '5',
                'answers-2-order': '3',
                'answers-3-text': '2',
                'answers-3-order': '4',
            },
        )
        self.assertEqual(response.status_code, 302)
        q = Question.objects.get(lesson=lesson)
        self.assertEqual(q.answers.count(), 4)
        self.assertEqual(Answer.objects.filter(question=q, is_correct=True).count(), 1)
