from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core import mail
from django.test import TestCase

from accounts.models import CustomUser


class PasswordResetTests(TestCase):
    def setUp(self):
        cache.clear()
        Site.objects.update_or_create(
            id=1,
            defaults={'domain': '127.0.0.1:8000', 'name': 'Recomeçar (dev)'},
        )
        self.user = CustomUser.objects.create_user(
            email='reset@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )

    def request_reset(self, email):
        return self.client.post('/senha/recuperar/', {'email': email})

    def test_existing_email_sends_one_message(self):
        response = self.request_reset(self.user.email)
        self.assertRedirects(response, '/senha/recuperar/enviado/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('127.0.0.1:8000', mail.outbox[0].body)
        self.assertIn('/senha/redefinir/', mail.outbox[0].body)

    def test_unknown_email_has_same_response_without_message(self):
        response = self.request_reset('missing@example.com')
        self.assertRedirects(response, '/senha/recuperar/enviado/')
        self.assertEqual(len(mail.outbox), 0)

    def test_inactive_user_does_not_receive_message(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.request_reset(self.user.email)
        self.assertEqual(len(mail.outbox), 0)

    def test_valid_link_changes_password_and_allows_login(self):
        self.request_reset(self.user.email)
        link = mail.outbox[0].body.split('/senha/redefinir/', 1)[1].splitlines()[0]
        uidb64, token = link.split('/')[:2]
        self.assertEqual(
            self.client.get(f'/senha/redefinir/{uidb64}/{token}/').status_code,
            302,
        )
        response = self.client.post(
            f'/senha/redefinir/{uidb64}/set-password/',
            {'new_password1': 'NovaSenhaForte123!', 'new_password2': 'NovaSenhaForte123!'},
        )
        self.assertRedirects(response, '/senha/redefinir/concluido/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NovaSenhaForte123!'))
        self.assertRedirects(
            self.client.post('/login/', {'username': self.user.email, 'password': 'NovaSenhaForte123!'}),
            '/painel/',
        )

    def test_invalid_token_does_not_change_password(self):
        self.request_reset(self.user.email)
        uidb64 = mail.outbox[0].body.split('/senha/redefinir/', 1)[1].split('/')[0]
        response = self.client.get(f'/senha/redefinir/{uidb64}/token-adulterado/')
        self.assertContains(response, 'inválido ou expirou')
        self.assertTrue(self.user.check_password('SenhaForte123!'))

    def test_weak_password_is_rejected(self):
        self.request_reset(self.user.email)
        link = mail.outbox[0].body.split('/senha/redefinir/', 1)[1].splitlines()[0]
        uidb64, token = link.split('/')[:2]
        self.client.get(f'/senha/redefinir/{uidb64}/{token}/')
        response = self.client.post(
            f'/senha/redefinir/{uidb64}/set-password/',
            {'new_password1': '123', 'new_password2': '123'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Esta senha é muito curta')
