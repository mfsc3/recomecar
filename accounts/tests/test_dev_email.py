from io import StringIO

from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.console import EmailBackend
from django.test import SimpleTestCase, override_settings

from accounts.dev_email import ReadableConsoleEmailBackend


class ReadableConsoleEmailBackendTests(SimpleTestCase):
    def email(self):
        url = (
            'http://127.0.0.1:8000/accounts/confirm-email/NA:1xT6co:'
            + 'a' * 56
            + '/'
        )
        return mail.EmailMessage(
            subject='Confirmação',
            body=f'Olá, ativar:\n{url}\nVocê já pode entrar.',
            from_email='no-reply@example.com',
            to=['ana@example.com'],
        ), url

    @override_settings(DEBUG=True)
    def test_imprime_corpo_decodificado_em_linhas_completas(self):
        message, url = self.email()
        stream = StringIO()
        backend = ReadableConsoleEmailBackend(stream=stream)

        backend.send_messages([message])
        output = stream.getvalue()

        self.assertIn(f'Subject: {message.subject}', output)
        self.assertIn(url, output)
        self.assertIn(f'\n{url}\n', output)
        self.assertIn('Olá', output)
        self.assertIn('Você', output)
        self.assertNotIn('=C3', output)
        self.assertNotIn('quoted-printable', output)

    @override_settings(DEBUG=False)
    def test_falha_fechada_fora_de_desenvolvimento(self):
        with self.assertRaises(ImproperlyConfigured):
            ReadableConsoleEmailBackend(stream=StringIO())

    def test_backend_console_padrao_quebra_url_longa(self):
        message, url = self.email()
        stream = StringIO()

        EmailBackend(stream=stream).send_messages([message])
        output = stream.getvalue()

        self.assertNotIn(f'\n{url}\n', output)
