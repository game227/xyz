"""Accounts tests — registration, login (incl. rate-limiting), role model."""
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .models import CustomUser, TeacherRating
from .views import LOGIN_ATTEMPT_LIMIT, REGISTER_LIMIT


class RegisterViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def _valid_payload(self, **overrides):
        payload = {
            'username': 'yangi_talaba',
            'first_name': 'Aziza',
            'last_name': 'Karimova',
            'email': 'aziza@example.com',
            'phone_number': '',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
        }
        payload.update(overrides)
        return payload

    def test_register_creates_student_and_logs_in(self):
        response = self.client.post(reverse('accounts:register'), self._valid_payload())
        self.assertEqual(response.status_code, 302)
        user = CustomUser.objects.get(username='yangi_talaba')
        self.assertEqual(user.role, CustomUser.Role.STUDENT)
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_register_duplicate_username_rejected(self):
        CustomUser.objects.create_user(username='band', password='pass12345')
        response = self.client.post(
            reverse('accounts:register'), self._valid_payload(username='band')
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='aziza@example.com').exists())

    def test_register_duplicate_email_rejected(self):
        CustomUser.objects.create_user(
            username='boshqa', password='pass12345', email='aziza@example.com'
        )
        response = self.client.post(reverse('accounts:register'), self._valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(email='aziza@example.com').count(), 1)

    def test_register_rate_limited_after_threshold(self):
        # Each attempt uses its own (unauthenticated) client — logging in after
        # a successful register would otherwise short-circuit the view before
        # the rate-limit check on later iterations. All requests share the
        # same test-client IP (127.0.0.1), which is what the limiter keys on.
        for i in range(REGISTER_LIMIT):
            Client().post(
                reverse('accounts:register'),
                self._valid_payload(username=f'user{i}', email=f'user{i}@example.com'),
            )
        blocked = Client().post(
            reverse('accounts:register'),
            self._valid_payload(username='blocked_user', email='blocked@example.com'),
        )
        self.assertEqual(blocked.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='blocked_user').exists())


class LoginViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.student = CustomUser.objects.create_user(
            username='talaba', password='talaba12345', role=CustomUser.Role.STUDENT
        )
        self.teacher = CustomUser.objects.create_user(
            username='ustoz', password='ustoz12345', role=CustomUser.Role.TEACHER
        )
        self.admin = CustomUser.objects.create_user(
            username='boshqaruvchi', password='admin12345',
            role=CustomUser.Role.ADMIN, is_staff=True, is_superuser=True,
        )

    def test_student_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('accounts:login'), {'username': 'talaba', 'password': 'talaba12345'}
        )
        self.assertRedirects(response, reverse('progress:dashboard'))

    def test_teacher_redirects_to_teacher_dashboard(self):
        response = self.client.post(
            reverse('accounts:login'), {'username': 'ustoz', 'password': 'ustoz12345'}
        )
        self.assertRedirects(response, reverse('teacher:dashboard'))

    def test_admin_redirects_to_admin_index(self):
        response = self.client.post(
            reverse('accounts:login'), {'username': 'boshqaruvchi', 'password': 'admin12345'}
        )
        self.assertRedirects(response, reverse('admin:index'))

    def test_wrong_password_does_not_log_in(self):
        response = self.client.post(
            reverse('accounts:login'), {'username': 'talaba', 'password': 'notogri'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_login_rate_limited_after_threshold(self):
        for _ in range(LOGIN_ATTEMPT_LIMIT):
            self.client.post(
                reverse('accounts:login'), {'username': 'talaba', 'password': 'notogri'}
            )
        blocked = self.client.post(
            reverse('accounts:login'), {'username': 'talaba', 'password': 'talaba12345'}
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertFalse(self.client.session.get('_auth_user_id'))


class CustomUserRolePropertyTests(TestCase):
    def test_role_properties(self):
        student = CustomUser.objects.create_user(username='s', password='p12345678')
        teacher = CustomUser.objects.create_user(
            username='t', password='p12345678', role=CustomUser.Role.TEACHER
        )
        admin = CustomUser.objects.create_user(
            username='a', password='p12345678', role=CustomUser.Role.ADMIN
        )

        self.assertTrue(student.is_student)
        self.assertFalse(student.can_manage_content)

        self.assertTrue(teacher.is_teacher)
        self.assertTrue(teacher.can_manage_content)

        self.assertTrue(admin.is_admin_role)
        self.assertTrue(admin.can_manage_content)


class TeacherRatingValidationTests(TestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            username='ustoz2', password='p12345678', role=CustomUser.Role.TEACHER
        )
        self.student = CustomUser.objects.create_user(username='talaba2', password='p12345678')

    def test_cannot_rate_self(self):
        rating = TeacherRating(
            student=self.teacher, teacher=self.teacher, stars=5,
        )
        with self.assertRaises(ValidationError):
            rating.clean()

    def test_stars_out_of_range_rejected(self):
        rating = TeacherRating(student=self.student, teacher=self.teacher, stars=6)
        with self.assertRaises(ValidationError):
            rating.clean()

    def test_valid_rating_passes_clean(self):
        rating = TeacherRating(student=self.student, teacher=self.teacher, stars=4)
        rating.clean()  # should not raise
