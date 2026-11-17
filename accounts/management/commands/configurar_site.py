import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Configura o domínio do Site usado pelos links de e-mail.'

    def handle(self, *args, **options):
        dominio = (
            os.environ.get('SITE_DOMAIN', '').strip()
            or os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
        )
        if not dominio:
            if not settings.DEBUG:
                raise CommandError(
                    'Defina SITE_DOMAIN para configurar o domínio do site.'
                )
            self.stdout.write(
                self.style.WARNING(
                    'SITE_DOMAIN ou RENDER_EXTERNAL_HOSTNAME não definido.'
                )
            )
            return

        Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={'domain': dominio, 'name': 'Recomeçar'},
        )
        self.stdout.write(dominio)
