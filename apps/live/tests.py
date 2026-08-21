"""Live watch/host access tests."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.live.models import LiveSession

User = get_user_model()


class LiveAccessTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher', password='teacher12345', role=User.Role.TEACHER
        )
        self.student = User.objects.create_user(
            username='student', password='student12345', role=User.Role.STUDENT
        )
        LiveSession.objects.create(
            title='Demo efir',
            host=self.teacher,
            platform=LiveSession.Platform.YOUTUBE,
            stream_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            status=LiveSession.Status.LIVE,
        )

    def test_guest_can_watch_live(self):
        response = self.client.get(reverse('live:watch'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo efir')

    def test_student_cannot_host(self):
        self.client.login(username='student', password='student12345')
        response = self.client.get(reverse('live:host'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/live/', response.url)

    def test_teacher_can_open_host(self):
        self.client.login(username='teacher', password='teacher12345')
        response = self.client.get(reverse('live:host'))
        self.assertEqual(response.status_code, 200)

    def test_youtube_embed_rendered_inline(self):
        """Platforma YouTube bo'lsa — video sahifa ichida iframe orqali ko'rinishi kerak."""
        response = self.client.get(reverse('live:watch'))
        self.assertContains(response, '<iframe')
        self.assertContains(response, 'youtube.com/embed/dQw4w9WgXcQ')

    def test_telegram_has_no_embed_only_external_link(self):
        """Telegram uchun iframe bo'lmasligi, tashqi havola chiqishi kerak."""
        LiveSession.objects.filter(platform=LiveSession.Platform.YOUTUBE).update(
            status=LiveSession.Status.ENDED
        )
        LiveSession.objects.create(
            title='Telegram efir',
            host=self.teacher,
            platform=LiveSession.Platform.TELEGRAM,
            stream_url='https://t.me/xyz_math/123',
            status=LiveSession.Status.LIVE,
        )
        response = self.client.get(reverse('live:watch'))
        self.assertNotContains(response, '<iframe')
        self.assertContains(response, 'https://t.me/xyz_math/123')
