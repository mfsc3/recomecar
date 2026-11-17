from io import BytesIO

from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from vagas.models import EmpresaProfile


def png_bytes():
    output = BytesIO()
    Image.new('RGB', (10, 10), 'white').save(output, format='PNG')
    return output.getvalue()


@override_settings(
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
)
class EmpresaPerfilTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='empresa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        self.perfil = EmpresaProfile.objects.create(
            user=self.user,
            cnpj='11222333000181',
            razao_social='Empresa Teste',
        )

    def test_empresa_edita_perfil_e_nao_adiciona_campos_admin(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('vagas:empresa_editar'),
            {
                'nome_fantasia': 'Empresa Fantasia',
                'endereco': 'Rua A, 10',
                'cidade': 'Recife',
                'estado': 'PE',
                'responsavel_nome': 'Maria',
                'telefone': '(81) 99999-9999',
                'descricao': 'Descrição institucional',
                'cnpj': '00000000000000',
                'razao_social': 'Adulterada',
                'is_aprovada': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.nome_fantasia, 'Empresa Fantasia')
        self.assertEqual(self.perfil.cnpj, '11222333000181')
        self.assertEqual(self.perfil.razao_social, 'Empresa Teste')
        self.assertFalse(self.perfil.is_aprovada)

    def test_upload_png_e_validacao_de_logo(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('vagas:empresa_editar'),
            {
                'nome_fantasia': 'Empresa',
                'endereco': '',
                'cidade': '',
                'estado': '',
                'responsavel_nome': '',
                'telefone': '',
                'descricao': '',
                'logo': SimpleUploadedFile(
                    'logo.png',
                    png_bytes(),
                    content_type='image/png',
                ),
            },
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            reverse('vagas:empresa_editar'),
            {
                'nome_fantasia': 'Empresa',
                'cidade': '',
                'estado': '',
                'telefone': '',
                'logo': SimpleUploadedFile(
                    'arquivo.txt',
                    b'texto',
                    content_type='text/plain',
                ),
            },
        )
        self.assertEqual(response.status_code, 200)

        grande = b'x' * (2 * 1024 * 1024 + 1)
        response = self.client.post(
            reverse('vagas:empresa_editar'),
            {
                'nome_fantasia': 'Empresa',
                'cidade': '',
                'estado': '',
                'telefone': '',
                'logo': SimpleUploadedFile(
                    'grande.png',
                    grande,
                    content_type='image/png',
                ),
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_telefone_invalido_e_campos_protegidos(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('vagas:empresa_editar'),
            {
                'nome_fantasia': 'Empresa',
                'cidade': 'Recife',
                'estado': 'PE',
                'telefone': 'abc',
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertNotIn('cnpj', form.fields)
        self.assertNotIn('razao_social', form.fields)
        self.assertNotIn('is_aprovada', form.fields)
