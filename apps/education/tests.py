"""Education tests — curriculum hierarchy ordering and active-only visibility."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import CustomUser

from .models import Course, Lesson, Module, Subject, Topic


class CurriculumOrderingTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name='Matematika')
        self.course_b = Course.objects.create(
            subject=self.subject, title='B kurs', order=2
        )
        self.course_a = Course.objects.create(
            subject=self.subject, title='A kurs', order=1
        )

    def test_courses_ordered_by_order_field_not_creation(self):
        titles = list(self.subject.courses.values_list('title', flat=True))
        self.assertEqual(titles, ['A kurs', 'B kurs'])

    def test_str_methods_are_human_readable(self):
        self.assertEqual(str(self.subject), 'Matematika')
        self.assertIn('Matematika', str(self.course_a))
        self.assertIn('A kurs', str(self.course_a))


class ActiveOnlyVisibilityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = CustomUser.objects.create_user(username='ko', password='pass12345')
        self.active_subject = Subject.objects.create(name='Faol fan', is_active=True)
        self.inactive_subject = Subject.objects.create(name='Nofaol fan', is_active=False)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse('education:subject_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_subject_list_excludes_inactive(self):
        self.client.login(username='ko', password='pass12345')
        response = self.client.get(reverse('education:subject_list'))
        subjects = list(response.context['subjects'])
        self.assertIn(self.active_subject, subjects)
        self.assertNotIn(self.inactive_subject, subjects)

    def test_inactive_subject_detail_returns_404(self):
        self.client.login(username='ko', password='pass12345')
        response = self.client.get(
            reverse('education:subject_detail', args=[self.inactive_subject.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_active_subject_detail_returns_200(self):
        self.client.login(username='ko', password='pass12345')
        response = self.client.get(
            reverse('education:subject_detail', args=[self.active_subject.pk])
        )
        self.assertEqual(response.status_code, 200)


class LessonFreeVideoValidationTests(TestCase):
    def test_lesson_requires_video_file(self):
        subject = Subject.objects.create(name='Fan')
        course = Course.objects.create(subject=subject, title='Kurs', order=1)
        module = Module.objects.create(course=course, title='Modul', order=1)
        topic = Topic.objects.create(module=module, title='Mavzu', order=1)
        video = SimpleUploadedFile('dars.mp4', b'fake-bytes', content_type='video/mp4')
        lesson = Lesson.objects.create(
            topic=topic, title='Dars 1', order=1, duration_minutes=5, video=video,
        )
        self.assertEqual(str(lesson), 'Mavzu — Dars 1')
        self.assertFalse(lesson.is_free_preview)
