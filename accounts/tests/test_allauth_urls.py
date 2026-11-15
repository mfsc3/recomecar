from django.test import TestCase

from accounts.models import CustomUser


class AllauthUrlTests(TestCase):
    def test_login_route_redirects_to_local_login(self):
        self.assertRedirects(self.client.get('/accounts/login/'), '/login/')

    def test_signup_get_and_post_redirect_without_creating_user(self):
        self.assertRedirects(self.client.get('/accounts/signup/'), '/cadastro/egressa/')
        self.assertRedirects(self.client.post('/accounts/signup/'), '/cadastro/egressa/')
        self.assertFalse(CustomUser.objects.exists())

    def test_password_reset_route_redirects_to_local_reset(self):
        self.assertRedirects(
            self.client.get('/accounts/password/reset/'),
            '/senha/recuperar/',
        )

    def test_google_login_requires_post(self):
        response = self.client.get('/accounts/google/login/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('accounts.google.com', response.get('Location', ''))

    def test_login_page_has_post_google_form_and_terms_notice(self):
        response = self.client.get('/login/')
        self.assertContains(response, 'method="post"')
        self.assertContains(response, 'Continuar com o Google')
        self.assertContains(response, 'Ao continuar com o Google, você aceita os')
        self.assertContains(response, 'href="/termos/"')
        self.assertContains(response, 'href="/privacidade/"')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_company_registration_has_no_google_button(self):
        response = self.client.get('/cadastro/empresa/')
        self.assertNotContains(response, 'Continuar com o Google')

    def test_extra_allauth_routes_redirect_to_panel(self):
        for path in (
            '/accounts/email/',
            '/accounts/password/change/',
            '/accounts/password/set/',
            '/accounts/3rdparty/',
        ):
            response = self.client.get(path)
            self.assertRedirects(response, '/painel/', fetch_redirect_response=False)

    def test_confirmation_route_is_not_redirected(self):
        response = self.client.get('/accounts/confirm-email/not-a-key/')
        self.assertEqual(response.status_code, 200)
