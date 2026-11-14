from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from accounts.models import CustomUser
from vagas.models import EmpresaProfile


class CadastroTests(TestCase):
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

    def empresa_data(self, **overrides):
        data = self.egressa_data(
            email='empresa@example.com',
            razao_social='Empresa Teste',
            cnpj='11.222.333/0001-81',
        )
        data.update(overrides)
        return data

    def test_egressa_is_created_with_fixed_role_and_consent(self):
        response = self.client.post('/cadastro/egressa/', self.egressa_data())
        self.assertRedirects(response, '/login/')
        user = CustomUser.objects.get(email='ana@example.com')
        self.assertEqual(user.role, CustomUser.Role.EGRESSA)
        self.assertTrue(user.aceitou_termo)
        self.assertTrue(user.check_password('SenhaForte123!'))

    def test_egressa_ignores_privileged_post_fields(self):
        response = self.client.post(
            '/cadastro/egressa/',
            self.egressa_data(role='ADMIN', is_staff='on', is_superuser='on'),
        )
        self.assertEqual(response.status_code, 302)
        user = CustomUser.objects.get(email='ana@example.com')
        self.assertEqual(user.role, CustomUser.Role.EGRESSA)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_egressa_requires_consent(self):
        data = self.egressa_data()
        data.pop('aceitou_termo')
        response = self.client.post('/cadastro/egressa/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='ana@example.com').exists())

    def test_egressa_rejects_different_passwords(self):
        response = self.client.post(
            '/cadastro/egressa/',
            self.egressa_data(password2='OutraSenha123!'),
        )
        self.assertEqual(response.status_code, 200)

    def test_egressa_rejects_weak_password(self):
        response = self.client.post(
            '/cadastro/egressa/',
            self.egressa_data(password1='123', password2='123'),
        )
        self.assertEqual(response.status_code, 200)

    def test_email_is_case_insensitive(self):
        CustomUser.objects.create_user(
            email='Ana@Example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        response = self.client.post(
            '/cadastro/egressa/',
            self.egressa_data(email='ana@example.com'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(email__iexact='ana@example.com').count(), 1)

    def test_empresa_uses_digits_only_and_fixed_role(self):
        response = self.client.post('/cadastro/empresa/', self.empresa_data())
        self.assertRedirects(response, '/login/')
        user = CustomUser.objects.get(email='empresa@example.com')
        self.assertEqual(user.role, CustomUser.Role.EMPRESA)
        profile = EmpresaProfile.objects.get(user=user)
        self.assertEqual(profile.cnpj, '11222333000181')
        self.assertTrue(user.aceitou_termo)

    def test_empresa_requires_consent(self):
        data = self.empresa_data()
        data.pop('aceitou_termo')
        response = self.client.post('/cadastro/empresa/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.exists())

    def test_empresa_ignores_role_tampering(self):
        response = self.client.post(
            '/cadastro/empresa/',
            self.empresa_data(role='ADMIN', is_staff='on', is_superuser='on'),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            CustomUser.objects.get(email='empresa@example.com').role,
            CustomUser.Role.EMPRESA,
        )

    def test_empresa_rejects_invalid_cnpj(self):
        for cnpj in ('11222333000182', '11111111111111'):
            response = self.client.post('/cadastro/empresa/', self.empresa_data(cnpj=cnpj))
            self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.exists())

    def test_empresa_rejects_duplicate_cnpj(self):
        self.client.post('/cadastro/empresa/', self.empresa_data())
        response = self.client.post(
            '/cadastro/empresa/',
            self.empresa_data(email='outra@example.com'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_empresa_creation_is_atomic(self):
        with patch.object(EmpresaProfile, 'save', side_effect=IntegrityError):
            response = self.client.post('/cadastro/empresa/', self.empresa_data())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='empresa@example.com').exists())
