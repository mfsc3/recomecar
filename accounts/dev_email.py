from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend


class ReadableConsoleEmailBackend(ConsoleEmailBackend):
    """Somente desenvolvimento: imprime o e-mail como texto puro."""

    def __init__(self, *args, **kwargs):
        if not settings.DEBUG:
            raise ImproperlyConfigured(
                'ReadableConsoleEmailBackend só pode ser usado com DEBUG=True.'
            )
        super().__init__(*args, **kwargs)

    def write_message(self, message):
        linhas = [
            f'Subject: {message.subject}',
            f'From: {message.from_email}',
            f'To: {", ".join(message.to)}',
            '',
            message.body,
            '-' * 79,
        ]
        self.stream.write('\n'.join(linhas) + '\n')
