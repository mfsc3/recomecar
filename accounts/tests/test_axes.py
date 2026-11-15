from django.test import TestCase

from accounts.models import CustomUser
from axes.models import AccessAttempt


class AxesTests(TestCase):
    def setUp(self):
        AccessAttempt.objects.all().delete()
        self.user = CustomUser.objects.create_user(
            email='axes@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
    def login(self, email, password):
        return self.client.post(
            '/login/',
            {'username': email, 'password': password},
        )
    def test_sixth_failure_is_blocked_even_with_correct_password(self):
        for _ in range(5):
            self.login(self.user.email, 'SenhaErrada123!')
        response = self.login(self.user.email, 'SenhaForte123!')
        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            'Muitas tentativas. Aguarde 15 minutos e tente novamente.',
            status_code=403,
        )

    def test_another_user_is_not_affected(self):
        other = CustomUser.objects.create_user(
            email='other@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        for _ in range(5):
            self.login(self.user.email, 'SenhaErrada123!')
        self.assertRedirects(
            self.login(other.email, 'SenhaForte123!'),
            '/painel/',
        )

    def test_success_before_limit_resets_counter(self):
        for _ in range(4):
            self.login(self.user.email, 'SenhaErrada123!')
        self.assertRedirects(
            self.login(self.user.email, 'SenhaForte123!'),
            '/painel/',
        )
        self.client.logout()
        for _ in range(4):
            response = self.login(self.user.email, 'SenhaErrada123!')
        self.assertEqual(response.status_code, 200)

    def test_unknown_email_is_blocked_without_account_enumeration(self):
        for _ in range(5):
            response = self.login('missing@example.com', 'SenhaErrada123!')
        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            'Muitas tentativas. Aguarde 15 minutos e tente novamente.',
            status_code=403,
        )

    def test_admin_login_is_blocked_after_five_failures(self):
        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        for _ in range(5):
            self.client.post(
                '/admin/login/',
                {'username': self.user.email, 'password': 'SenhaErrada123!'},
            )
        response = self.client.post(
            '/admin/login/',
            {'username': self.user.email, 'password': 'SenhaErrada123!'},
        )
        self.assertEqual(response.status_code, 403)

