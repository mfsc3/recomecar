import re
from unittest.mock import patch

from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache
from django.test import TestCase

from allauth.account.models import EmailAddress


class MensagensTests(TestCase):
    def setUp(self):
        cache.clear()
        Site.objects.update_or_create(
            id=1,
            defaults={'domain': 'testserver', 'name': 'Recomeçar'},
        )

    def egressa_data(self, **overrides):
        data = {
            'first_name': 'Ana',
            'email': 'ana@example.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
            'aceitou_termo': 'on',
        }
        data.update(overrides)
        return data

    def test_sucesso_tem_auto_dismiss(self):
        response = self.client.post(
            '/cadastro/egressa/',
            self.egressa_data(),
            follow=True,
        )

        self.assertRedirects(response, '/login/')
        self.assertRegex(
            response.content.decode(),
            r'<li[^>]*data-auto-dismiss[^>]*>',
        )

    @patch.object(
        EmailAddress,
        'send_confirmation',
        side_effect=RuntimeError('mail unavailable'),
    )
    def test_aviso_de_falha_nao_tem_auto_dismiss(self, _send):
        response = self.client.post(
            '/cadastro/egressa/',
            self.egressa_data(),
            follow=True,
        )
        html = response.content.decode()

        self.assertContains(response, 'não conseguimos enviar o e-mail')
        self.assertEqual(
            re.findall(r'<li[^>]*data-auto-dismiss[^>]*>', html),
            [],
        )

    def test_login_contem_link_de_reenvio(self):
        response = self.client.get('/login/')

        self.assertContains(response, 'href="/email/reenviar/"')
