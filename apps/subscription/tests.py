"""Subscription request admin actions and activation flow."""
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from apps.subscription.admin import SubscriptionRequestAdmin
from apps.subscription.models import Subscription, SubscriptionRequest
from apps.subscription.services import has_active_subscription

User = get_user_model()


class SubscriptionRequestAdminTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@xyz.uz', password='admin12345'
        )
        self.student = User.objects.create_user(
            username='student', email='s@xyz.uz', password='student12345'
        )
        self.site = AdminSite()
        self.model_admin = SubscriptionRequestAdmin(SubscriptionRequest, self.site)

    def _action_request(self):
        request = self.factory.post('/admin/')
        request.user = self.admin_user
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        return request

    def test_approve_and_activate_grants_subscription(self):
        req = SubscriptionRequest.objects.create(
            user=self.student,
            full_name='Talaba',
            phone='+998901112233',
            plan_days=30,
            status=SubscriptionRequest.Status.NEW,
        )
        request = self._action_request()
        self.model_admin.approve_and_activate(request, SubscriptionRequest.objects.filter(pk=req.pk))

        req.refresh_from_db()
        self.assertEqual(req.status, SubscriptionRequest.Status.DONE)
        self.assertTrue(has_active_subscription(self.student))
        sub = Subscription.objects.filter(user=self.student, status=Subscription.Status.ACTIVE).first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.duration_days, 30)

    def test_approve_skips_unlinked_user(self):
        req = SubscriptionRequest.objects.create(
            user=None,
            full_name='Anonim',
            phone='+998909998877',
            plan_days=30,
        )
        request = self._action_request()
        self.model_admin.approve_and_activate(request, SubscriptionRequest.objects.filter(pk=req.pk))
        req.refresh_from_db()
        self.assertEqual(req.status, SubscriptionRequest.Status.NEW)
        self.assertFalse(Subscription.objects.exists())

    def test_reject_requests(self):
        req = SubscriptionRequest.objects.create(
            user=self.student,
            full_name='Talaba',
            phone='+998901112233',
            plan_days=90,
        )
        request = self._action_request()
        self.model_admin.reject_requests(request, SubscriptionRequest.objects.filter(pk=req.pk))
        req.refresh_from_db()
        self.assertEqual(req.status, SubscriptionRequest.Status.REJECTED)
