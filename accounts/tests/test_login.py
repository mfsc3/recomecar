from django.test import TestCase

from accounts.models import CustomUser


class LoginTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='login@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )

    def form_error(self, response):
        return str(response.context['form'].non_field_errors()[0])

    def test_login_accepts_any_email_case(self):
        response = self.client.post(
            '/login/',
            {'username': 'LOGIN@EXAMPLE.COM', 'password': 'SenhaForte123!'},
        )
        self.assertRedirects(response, '/painel/')

    def test_unknown_email_and_wrong_password_have_same_message(self):
        unknown = self.client.post(
            '/login/',
            {'username': 'unknown@example.com', 'password': 'SenhaForte123!'},
        )
        wrong_password = self.client.post(
            '/login/',
            {'username': 'login@example.com', 'password': 'SenhaErrada123!'},
        )
        self.assertEqual(self.form_error(unknown), self.form_error(wrong_password))
        self.assertEqual(self.form_error(unknown), 'E-mail ou senha incorretos.')

    def test_inactive_account_has_same_message(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        response = self.client.post(
            '/login/',
            {'username': 'login@example.com', 'password': 'SenhaForte123!'},
        )
        self.assertEqual(self.form_error(response), 'E-mail ou senha incorretos.')

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.assertRedirects(self.client.post('/logout/'), '/login/')

    def test_external_next_is_not_used(self):
        response = self.client.post(
            '/login/?next=https://site-externo.com',
            {'username': 'login@example.com', 'password': 'SenhaForte123!'},
        )
        self.assertRedirects(response, '/painel/')

    def test_authenticated_user_is_redirected_from_login(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get('/login/'), '/painel/')

    def test_panel_requires_login(self):
        response = self.client.get('/painel/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/?next=', response['Location'])
