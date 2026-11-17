import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Cria o primeiro administrador de forma idempotente.'

    def handle(self, *args, **options):
        user_model = get_user_model()
        if user_model.objects.filter(is_superuser=True).exists():
            self.stdout.write('Administrador já existe')
            return

        email = os.environ.get('ADMIN_EMAIL', '').strip()
        password = os.environ.get('ADMIN_INITIAL_PASSWORD', '')
        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    'ADMIN_EMAIL e ADMIN_INITIAL_PASSWORD não definidos; '
                    'administrador inicial não criado.'
                )
            )
            return

        user = user_model(email=email)
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            raise CommandError('A senha inicial não atende aos requisitos.') from exc

        user_model.objects.create_superuser(email=email, password=password)
        self.stdout.write('Administrador inicial criado')
