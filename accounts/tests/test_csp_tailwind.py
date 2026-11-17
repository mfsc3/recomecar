from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class CspTailwindTests(TestCase):
    def test_base_nao_contem_cdn_tailwind(self):
        for url in (reverse('vagas:lista'), reverse('accounts:login')):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertNotContains(response, 'cdn.tailwindcss.com')

    def test_base_contem_link_local_tailwind(self):
        response = self.client.get(reverse('vagas:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'css/tailwind.css')
        self.assertContains(response, 'rel="stylesheet"')

    def test_header_csp_presente_em_rota_publica(self):
        response = self.client.get(reverse('vagas:lista'))
        self.assertIn('Content-Security-Policy', response.headers)
        csp = response.headers['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)
        self.assertNotIn('unsafe-inline', csp)
        self.assertNotIn('unsafe-eval', csp)

    def test_header_csp_ausente_em_admin(self):
        response = self.client.get('/admin/login/')
        self.assertNotIn('Content-Security-Policy', response)

    def test_settings_tem_staticfiles_dirs_e_csp_middleware(self):
        self.assertIn('csp', settings.INSTALLED_APPS)
        self.assertIn('csp.middleware.CSPMiddleware', settings.MIDDLEWARE)
        static_dirs = [str(p) for p in settings.STATICFILES_DIRS]
        self.assertTrue(
            any(p.endswith('static') for p in static_dirs),
            f'STATICFILES_DIRS não contém static/: {static_dirs}',
        )
