from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialLogin

from accounts.adapters import CustomSocialAccountAdapter
from accounts.models import CustomUser


class SocialVerifiedLinkTests(TestCase):
    def setUp(self):
        self.adapter = CustomSocialAccountAdapter()
        self.request = RequestFactory().get('/accounts/google/login/')
        self.request.session = {}
        self.request._messages = FallbackStorage(self.request)

    def sociallogin(self, email, is_existing=False, verified=True):
        user = CustomUser(email=email)
        address = SimpleNamespace(email=email, verified=verified)
        social = SimpleNamespace(
            is_existing=is_existing,
            user=user,
            email_addresses=[address],
        )
        if is_existing:
            social.connect = SocialLogin.connect
        return social

    def test_email_verificado_permite_link(self):
        existing = CustomUser.objects.create_user(
            email='verificado@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        EmailAddress.objects.create(
            user=existing,
            email=existing.email,
            primary=True,
            verified=True,
        )
        social = self.sociallogin(existing.email)
        social.connect = lambda request, user: None
        with patch.object(social, 'connect', wraps=social.connect) as connect:
            self.adapter.pre_social_login(self.request, social)
        connect.assert_called_once_with(self.request, existing)

    def test_email_nao_verificado_bloqueia(self):
        existing = CustomUser.objects.create_user(
            email='nao-verificado@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        EmailAddress.objects.create(
            user=existing,
            email=existing.email,
            primary=True,
            verified=False,
        )
        social = self.sociallogin(existing.email)
        with self.assertRaises(ImmediateHttpResponse):
            self.adapter.pre_social_login(self.request, social)

    def test_email_inexistente_permite_cadastro_novo(self):
        social = self.sociallogin('novo@example.com')
        self.adapter.pre_social_login(self.request, social)

    def test_social_existente_inativo_bloqueia(self):
        existing = CustomUser.objects.create_user(
            email='inativo@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
            is_active=False,
        )
        social = self.sociallogin(existing.email, is_existing=True)
        social.user = existing
        with self.assertRaises(ImmediateHttpResponse):
            self.adapter.pre_social_login(self.request, social)

    def test_social_existente_ativo_passa(self):
        existing = CustomUser.objects.create_user(
            email='ativo@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
            is_active=True,
        )
        social = self.sociallogin(existing.email, is_existing=True)
        social.user = existing
        self.adapter.pre_social_login(self.request, social)
