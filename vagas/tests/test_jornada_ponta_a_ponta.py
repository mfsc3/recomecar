from io import BytesIO

from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Curriculo, CustomUser, Experiencia
from vagas.models import Candidatura, EmpresaProfile


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
class JornadaPontaAPontaTests(TestCase):
    def test_jornada_completa_e_snapshot_immutavel(self):
        empresa_user = CustomUser.objects.create_user(
            email='empresa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        perfil = EmpresaProfile.objects.create(
            user=empresa_user,
            cnpj='11222333000181',
            razao_social='Empresa Jornada',
        )

        self.client.force_login(empresa_user)
        response = self.client.post(
            reverse('vagas:empresa_editar'),
            {
                'nome_fantasia': 'Fantasia Jornada',
                'logo': SimpleUploadedFile(
                    'logo.png',
                    png_bytes(),
                    content_type='image/png',
                ),
                'endereco': 'Rua das Flores, 10',
                'cidade': 'Recife',
                'estado': 'PE',
                'responsavel_nome': 'Responsável',
                'telefone': '(81) 99999-9999',
                'descricao': 'Empresa de exemplo',
            },
        )
        self.assertEqual(response.status_code, 302)
        perfil.refresh_from_db()
        perfil.is_aprovada = True
        perfil.save()

        response = self.client.post(
            reverse('vagas:criar'),
            {
                'titulo': 'Analista',
                'descricao': 'Descrição da vaga',
                'requisitos': 'Experiência',
                'salario': '',
                'ativa': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)

        egressa = CustomUser.objects.create_user(
            email='egressa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        self.client.force_login(egressa)
        curriculo = Curriculo.objects.create(
            user=egressa,
            resumo='Resumo da candidata',
            habilidades='Python',
        )
        response = self.client.post(
            reverse('accounts:experiencia_nova'),
            {
                'empresa_nome': 'Empresa Y',
                'cargo': 'Cargo X',
                'data_inicio': '2024-01-01',
                'data_fim': '',
                'descricao': 'Atividades',
            },
        )
        self.assertEqual(response.status_code, 302)

        vaga = perfil.vagas.get()
        response = self.client.post(
            reverse('vagas:candidatar', args=[vaga.pk])
        )
        self.assertEqual(response.status_code, 302)
        candidatura = Candidatura.objects.get(vaga=vaga, candidata=egressa)

        self.client.force_login(empresa_user)
        response = self.client.get(
            reverse(
                'vagas:candidata_curriculo',
                args=[vaga.pk, candidatura.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cargo X')
        self.assertContains(response, 'Empresa Y')

        self.client.force_login(egressa)
        experiencia = curriculo.experiencias.get()
        response = self.client.post(
            reverse('accounts:experiencia_editar', args=[experiencia.pk]),
            {
                'empresa_nome': 'Empresa Y',
                'cargo': 'Cargo Editado',
                'data_inicio': '2024-01-01',
                'data_fim': '',
                'descricao': 'Nova atividade',
            },
        )
        self.assertEqual(response.status_code, 302)

        self.client.force_login(empresa_user)
        response = self.client.get(
            reverse(
                'vagas:candidata_curriculo',
                args=[vaga.pk, candidatura.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cargo X')
        self.assertNotContains(response, 'Cargo Editado')
