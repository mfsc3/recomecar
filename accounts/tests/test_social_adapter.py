from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory, TestCase

from allauth.account.models import EmailAddress
from allauth.core import context
from allauth.core.exceptions import ImmediateHttpResponse, SignupClosedException
from allauth.socialaccount.internal.flows.signup import process_signup
from allauth.socialaccount.models import SocialAccount, SocialLogin

from accounts.adapters import CustomAccountAdapter, CustomSocialAccountAdapter
from accounts.models import CustomUser


class SocialAdapterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()

    def request(self):
        request = self.factory.get('/accounts/google/login/')
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def login(self, user=None, email='google@example.com', verified=True, existing=False):
        return SimpleNamespace(
            user=user or CustomUser(email=email),
            email_addresses=[SimpleNamespace(email=email, verified=verified)],
            is_existing=existing,
        )

    def assert_blocked(self, sociallogin):
        with self.assertRaises(ImmediateHttpResponse) as caught:
            self.adapter.pre_social_login(self.request(), sociallogin)
        self.assertEqual(caught.exception.response.status_code, 302)
        self.assertEqual(caught.exception.response['Location'], '/login/')

    def test_new_user_is_forced_to_egressa_and_email_is_normalized(self):
        sociallogin = self.login(email='  Google@Example.COM ')
        user = self.adapter.populate_user(
            self.request(), sociallogin, {'email': 'attacker@example.com', 'role': 'ADMIN'}
        )
        self.assertEqual(user.email, 'google@example.com')
        self.assertEqual(user.role, CustomUser.Role.EGRESSA)
        self.assertTrue(user.aceitou_termo)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertFalse(user.has_usable_password())

    def test_social_signup_is_open_but_local_signup_is_closed(self):
        request = self.request()
        sociallogin = self.login()

        self.assertTrue(self.adapter.is_open_for_signup(request, sociallogin))
        self.assertFalse(CustomAccountAdapter().is_open_for_signup(request))

    def test_process_signup_creates_restricted_egressa(self):
        request = self.factory.get('/accounts/google/login/callback/')
        get_response = lambda request: None
        SessionMiddleware(get_response).process_request(request)
        request.session.save()
        MessageMiddleware(get_response).process_request(request)
        request.user = AnonymousUser()
        sociallogin = SocialLogin(
            user=CustomUser(email='new-google@example.com'),
            account=SocialAccount(provider='google', uid='new-google-user'),
            email_addresses=[
                EmailAddress(email='new-google@example.com', verified=True),
            ],
        )

        try:
            with context.request_context(request):
                process_signup(request, sociallogin)
        except SignupClosedException as exc:
            self.fail(f'process_signup() unexpectedly raised SignupClosedException: {exc}')

        user = CustomUser.objects.get(email='new-google@example.com')
        self.assertEqual(user.role, CustomUser.Role.EGRESSA)
        self.assertTrue(user.aceitou_termo)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_usable_password())
    def test_extra_data_cannot_elevate_social_user(self):
        sociallogin = self.login()
        user = self.adapter.populate_user(
            self.request(), sociallogin, {'role': 'ADMIN', 'is_staff': True, 'is_superuser': True}
        )
        self.assertEqual(user.role, CustomUser.Role.EGRESSA)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_unverified_email_is_blocked(self):
        self.assert_blocked(self.login(verified=False))

    def test_existing_local_email_is_blocked_without_linking(self):
        CustomUser.objects.create_user(
            email='google@example.com', password='SenhaForte123!', role=CustomUser.Role.EGRESSA
        )
        self.assert_blocked(self.login())
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_existing_company_email_is_blocked(self):
        company = CustomUser.objects.create_user(
            email='google@example.com', password='SenhaForte123!', role=CustomUser.Role.EMPRESA
        )
        self.assert_blocked(self.login(user=company, existing=True))

    def test_existing_admin_email_is_blocked(self):
        admin = CustomUser.objects.create_superuser(
            email='google@example.com', password='SenhaForte123!'
        )
        self.assert_blocked(self.login(user=admin, existing=True))

    def test_existing_active_egressa_is_allowed(self):
        user = CustomUser.objects.create_user(
            email='google@example.com', password='SenhaForte123!', role=CustomUser.Role.EGRESSA
        )
        self.adapter.pre_social_login(self.request(), self.login(user=user, existing=True))

    def test_existing_inactive_egressa_is_blocked(self):
        user = CustomUser.objects.create_user(
            email='google@example.com', password='SenhaForte123!', role=CustomUser.Role.EGRESSA,
            is_active=False,
        )
        self.assert_blocked(self.login(user=user, existing=True))

    def test_existing_non_egressa_is_blocked(self):
        user = CustomUser.objects.create_user(
            email='google@example.com', password='SenhaForte123!', role=CustomUser.Role.EMPRESA,
        )
        self.assert_blocked(self.login(user=user, existing=True))

    def test_save_user_reapplies_restricted_fields(self):
        user = CustomUser(email='Google@Example.COM', role=CustomUser.Role.ADMIN)
        sociallogin = SocialLogin(user=user)
        with patch('allauth.socialaccount.adapter.DefaultSocialAccountAdapter.save_user', return_value=user):
            result = self.adapter.save_user(self.request(), sociallogin)
        self.assertIs(result, user)
        self.assertEqual(user.role, CustomUser.Role.EGRESSA)
        self.assertTrue(user.aceitou_termo)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertFalse(user.has_usable_password())
