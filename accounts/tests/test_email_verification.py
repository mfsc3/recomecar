import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache
from django.core.signing import SignatureExpired
from django.test import TestCase
from django.utils import timezone

from allauth.account.models import EmailAddress
from allauth.core import context
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.internal.flows.signup import process_signup


User = get_user_model()


class EmailVerificationTests(TestCase):
    def setUp(self):
        cache.clear()
        Site.objects.update_or_create(
            id=1,
            defaults={'domain': 'testserver', 'name': 'Recomeçar'},
        )

    def egressa_data(self, **overrides):
        data = {
            'first_name': 'Ana',
            'email': 'ana@example.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
            'aceitou_termo': 'on',
        }
        data.update(overrides)
        return data

    def empresa_data(self, **overrides):
        data = self.egressa_data(
            email='empresa@example.com',
            razao_social='Empresa Teste',
            cnpj='11.222.333/0001-81',
        )
        data.update(overrides)
        return data

    def confirmation_path(self):
        match = re.search(
            r'https?://[^/]+(/accounts/confirm-email/[^/\s]+/)',
            mail.outbox[0].body,
        )
        self.assertIsNotNone(match)
        return match.group(1)

    def test_egressa_signup_creates_pending_address_and_message(self):
        self.client.post('/cadastro/egressa/', self.egressa_data())
        user = User.objects.get(email='ana@example.com')
        address = EmailAddress.objects.get(user=user)
        self.assertFalse(user.is_active)
        self.assertFalse(address.verified)
        self.assertTrue(address.primary)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('testserver', mail.outbox[0].body)

    def test_empresa_signup_creates_pending_address_and_message(self):
        self.client.post('/cadastro/empresa/', self.empresa_data())
        user = User.objects.get(email='empresa@example.com')
        address = EmailAddress.objects.get(user=user)
        self.assertFalse(user.is_active)
        self.assertFalse(address.verified)
        self.assertTrue(address.primary)
        self.assertEqual(len(mail.outbox), 1)

    def test_pending_login_uses_generic_message(self):
        self.client.post('/cadastro/egressa/', self.egressa_data())
        response = self.client.post(
            '/login/',
            {'username': 'ana@example.com', 'password': 'SenhaForte123!'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'E-mail ou senha incorretos.')

    def test_real_confirmation_requires_post_and_allows_login(self):
        self.client.post('/cadastro/egressa/', self.egressa_data())
        path = self.confirmation_path()
        self.assertEqual(self.client.get(path).status_code, 200)
        user = User.objects.get(email='ana@example.com')
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        response = self.client.post(path)
        self.assertRedirects(response, '/login/')
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(EmailAddress.objects.get(user=user).verified)
        self.assertRedirects(
            self.client.post(
                '/login/',
                {'username': user.email, 'password': 'SenhaForte123!'},
            ),
            '/painel/',
        )

    def test_adulterated_confirmation_does_not_activate(self):
        self.client.post('/cadastro/egressa/', self.egressa_data())
        path = self.confirmation_path()
        key = path.rstrip('/').rsplit('/', 1)[-1]
        adulterated = key[:-1] + ('a' if key[-1] != 'a' else 'b')
        self.client.post(f'/accounts/confirm-email/{adulterated}/')
        self.assertFalse(User.objects.get(email='ana@example.com').is_active)

    def test_expired_confirmation_does_not_activate(self):
        self.client.post('/cadastro/egressa/', self.egressa_data())
        path = self.confirmation_path()
        with patch(
            'allauth.account.models.signing.loads',
            side_effect=SignatureExpired,
        ):
            self.client.post(path)
        self.assertFalse(User.objects.get(email='ana@example.com').is_active)

    def test_receiver_does_not_activate_restricted_users(self):
        cases = (
            ('admin', User.Role.ADMIN, {'is_staff': False, 'is_superuser': False}),
            ('staff', User.Role.EGRESSA, {'is_staff': True, 'is_superuser': False}),
            ('superuser', User.Role.EMPRESA, {'is_staff': False, 'is_superuser': True}),
            ('logged', User.Role.EGRESSA, {'is_staff': False, 'is_superuser': False, 'last_login': 'now'}),
        )
        for name, role, extra in cases:
            if extra.get('last_login') == 'now':
                extra['last_login'] = timezone.now()
            user = User.objects.create_user(
                email=f'{name}@example.com',
                password='SenhaForte123!',
                role=role,
                is_active=False,
                **extra,
            )
            address = EmailAddress.objects.create(
                user=user,
                email=user.email,
                primary=True,
                verified=False,
            )
            from allauth.account import signals

            signals.email_confirmed.send(sender=EmailAddress, request=None, email_address=address)
            user.refresh_from_db()
            self.assertFalse(user.is_active)

    @patch(
        'accounts.email_verification.send_verification_email_to_address',
        side_effect=RuntimeError('mail unavailable'),
    )
    def test_email_failure_keeps_created_user_and_returns_warning(self, _send):
        response = self.client.post('/cadastro/egressa/', self.egressa_data())
        self.assertRedirects(response, '/login/')
        self.assertTrue(User.objects.filter(email='ana@example.com').exists())
        self.assertEqual(response.wsgi_request._messages._queued_messages[0].level, 30)

    def test_google_signup_remains_active_with_verified_address(self):
        request = self.client.get('/login/').wsgi_request
        sociallogin = SocialLogin(
            user=User(email='google@example.com'),
            account=SocialAccount(provider='google', uid='google-1'),
            email_addresses=[
                EmailAddress(email='google@example.com', verified=True, primary=True),
            ],
        )
        with context.request_context(request):
            process_signup(request, sociallogin)
        user = User.objects.get(email='google@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(EmailAddress.objects.get(user=user).verified)
