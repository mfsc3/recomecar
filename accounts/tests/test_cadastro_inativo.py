from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from allauth.account.models import EmailAddress

from vagas.models import EmpresaProfile


User = get_user_model()


class CadastroInativoTests(TestCase):
    def egressa_data(self):
        return {
            'first_name': 'Ana',
            'email': 'ana@example.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
            'aceitou_termo': 'on',
        }

    def empresa_data(self):
        return {
            'first_name': 'Maria',
            'email': 'empresa@example.com',
            'razao_social': 'Empresa Teste',
            'cnpj': '11.222.333/0001-81',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
            'aceitou_termo': 'on',
        }

    def test_cadastro_egressa_cria_user_inativo(self):
        response = self.client.post('/cadastro/egressa/', self.egressa_data())
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='ana@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(user.role, User.Role.EGRESSA)

    def test_cadastro_egressa_cria_email_address_nao_verificado(self):
        self.client.post('/cadastro/egressa/', self.egressa_data())
        user = User.objects.get(email='ana@example.com')
        address = EmailAddress.objects.get(user=user)
        self.assertFalse(address.verified)
        self.assertTrue(address.primary)

    def test_cadastro_egressa_envia_email(self):
        self.client.post('/cadastro/egressa/', self.egressa_data())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('confirm-email', mail.outbox[0].body)

    def test_cadastro_egressa_nao_loga_antes_de_confirmar(self):
        self.client.post('/cadastro/egressa/', self.egressa_data())
        response = self.client.post(
            '/login/',
            {'username': 'ana@example.com', 'password': 'SenhaForte123!'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cadastro_empresa_cria_user_inativo_e_empresaprofile(self):
        response = self.client.post('/cadastro/empresa/', self.empresa_data())
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='empresa@example.com')
        self.assertFalse(user.is_active)
        self.assertTrue(EmpresaProfile.objects.filter(user=user).exists())

    @patch.object(
        EmailAddress,
        'send_confirmation',
        side_effect=RuntimeError('mail unavailable'),
    )
    def test_cadastro_com_falha_smtp_cria_user_mas_nao_quebra(self, _send):
        response = self.client.post('/cadastro/egressa/', self.egressa_data())
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='ana@example.com')
        self.assertFalse(user.is_active)
        queued = list(response.wsgi_request._messages)
        self.assertTrue(
            any('não conseguimos enviar' in str(message) for message in queued)
        )
