from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase


User = get_user_model()


class RateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email='reset@example.com',
            password='SenhaForte123!',
            role=User.Role.EGRESSA,
        )

    def reset(self, email, ip='10.0.0.1'):
        return self.client.post(
            '/senha/recuperar/',
            {'email': email},
            REMOTE_ADDR=ip,
        )

    def test_sixth_request_from_same_ip_returns_429(self):
        for _ in range(5):
            self.reset('missing@example.com')
        self.assertEqual(self.reset('missing@example.com').status_code, 429)

    def test_fourth_request_for_same_email_suppresses_message(self):
        responses = [self.reset(self.user.email) for _ in range(4)]
        self.assertEqual(responses[0].content, responses[-1].content)
        self.assertEqual(len(mail.outbox), 3)

    def test_existing_and_unknown_emails_count_equally(self):
        for _ in range(3):
            self.reset(self.user.email)
        self.assertEqual(self.reset(self.user.email).status_code, 302)
        for _ in range(3):
            self.reset('missing@example.com', ip='10.0.0.2')
        self.assertEqual(
            self.reset('missing@example.com', ip='10.0.0.2').status_code,
            302,
        )
        self.assertEqual(len(mail.outbox), 3)

    def test_different_ips_are_independent(self):
        for index in range(5):
            response = self.reset('missing@example.com', ip=f'10.0.0.{index + 1}')
            self.assertEqual(response.status_code, 302)
