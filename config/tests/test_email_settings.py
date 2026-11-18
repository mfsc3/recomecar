from django.conf import settings
from django.test import SimpleTestCase


class EmailSettingsTests(SimpleTestCase):
    def test_default_from_email_configurado(self):
        self.assertIn('recomecar.app', settings.DEFAULT_FROM_EMAIL)

    @property
    def debug_is_true(self):
        return settings.DEBUG

    def test_email_backend_console_em_debug(self):
        if not settings.DEBUG:
            self.skipTest('DEBUG=False')
        self.assertEqual(
            settings.EMAIL_BACKEND,
            'django.core.mail.backends.console.EmailBackend',
        )

    def test_email_backend_smtp_em_producao(self):
        if settings.DEBUG or 'locmem' in settings.EMAIL_BACKEND:
            self.skipTest('Ambiente de teste ou DEBUG=True')
        self.assertEqual(
            settings.EMAIL_BACKEND,
            'django.core.mail.backends.smtp.EmailBackend',
        )
