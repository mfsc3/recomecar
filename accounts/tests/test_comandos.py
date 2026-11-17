import os
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.management import call_command, CommandError
from django.test import TestCase
from django.contrib.sites.models import Site

from accounts.models import CustomUser


class ManagementCommandTests(TestCase):
    @patch.dict(os.environ, {'SITE_DOMAIN': 'recomecar.example'}, clear=False)
    def test_configurar_site_is_idempotent(self):
        call_command('configurar_site')
        call_command('configurar_site')

        site = Site.objects.get(pk=settings.SITE_ID)
        self.assertEqual(site.domain, 'recomecar.example')
        self.assertEqual(Site.objects.filter(pk=settings.SITE_ID).count(), 1)

    @patch.dict(os.environ, {}, clear=False)
    def test_configurar_site_fails_closed_outside_debug(self):
        with patch.dict(os.environ, {'SITE_DOMAIN': ''}, clear=False):
            with self.assertRaises(CommandError):
                call_command('configurar_site')

    @patch.dict(
        os.environ,
        {
            'ADMIN_EMAIL': 'admin@example.com',
            'ADMIN_INITIAL_PASSWORD': 'Admin-Initial-2026!x',
        },
        clear=False,
    )
    def test_criar_admin_inicial_is_idempotent_and_does_not_email(self):
        call_command('criar_admin_inicial')
        call_command('criar_admin_inicial')

        self.assertEqual(
            CustomUser.objects.filter(
                email='admin@example.com',
                is_superuser=True,
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 0)
