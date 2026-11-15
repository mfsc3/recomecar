import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache
from django.test import TestCase

from allauth.account.models import EmailAddress


User = get_user_model()


class ReenvioTests(TestCase):
    def setUp(self):
        cache.clear()
        Site.objects.update_or_create(
            id=1,
            defaults={'domain': 'testserver', 'name': 'Recomeçar'},
        )

    def pending(self):
        user = User.objects.create_user(
            email='pending@example.com',
            password='SenhaForte123!',
            role=User.Role.EGRESSA,
            is_active=False,
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=False,
        )
        return user

    def post(self, email):
        return self.client.post('/email/reenviar/', {'email': email})

    def test_pending_account_receives_one_message(self):
        self.pending()
        response = self.post('pending@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_unknown_active_and_admin_accounts_have_same_response(self):
        pending_response = self.post('missing@example.com')
        active = User.objects.create_user(
            email='active@example.com',
            password='SenhaForte123!',
            role=User.Role.EGRESSA,
        )
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='SenhaForte123!',
        )
        active_response = self.post(active.email)
        admin_response = self.post(admin.email)
        for response in (pending_response, active_response, admin_response):
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                'Se houver uma conta aguardando confirmação, enviaremos um novo e-mail.',
            )
        self.assertEqual(len(mail.outbox), 0)

    def test_ip_limit_returns_429(self):
        self.pending()
        for _ in range(5):
            response = self.post('pending@example.com')
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post('pending@example.com').status_code, 429)

    @patch(
        'accounts.views.send_verification_email_to_address',
        return_value=True,
    )
    def test_email_limit_suppresses_send_without_changing_response(self, send):
        self.pending()
        responses = [self.post('pending@example.com') for _ in range(4)]
        first_content = re.sub(
            rb'name="csrfmiddlewaretoken" value="[^"]+"',
            b'name="csrfmiddlewaretoken" value=""',
            responses[0].content,
        )
        for response in responses:
            content = re.sub(
                rb'name="csrfmiddlewaretoken" value="[^"]+"',
                b'name="csrfmiddlewaretoken" value=""',
                response.content,
            )
            self.assertEqual(content, first_content)
        self.assertEqual(send.call_count, 3)
