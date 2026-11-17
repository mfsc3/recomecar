from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Curriculo, CustomUser, Escolaridade, Experiencia


class CurriculoTests(TestCase):
    def setUp(self):
        self.egressa_a = CustomUser.objects.create_user(
            email='a@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        self.egressa_b = CustomUser.objects.create_user(
            email='b@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )

    def test_egressa_cria_edita_e_acessa_curriculo(self):
        self.client.force_login(self.egressa_a)
        detail = self.client.get(reverse('accounts:curriculo'))
        self.assertEqual(detail.status_code, 200)
        response = self.client.post(
            reverse('accounts:curriculo_editar'),
            {'resumo': 'Resumo X', 'habilidades': 'Python, Django'},
        )
        self.assertRedirects(response, reverse('accounts:curriculo'))
        curriculo = Curriculo.objects.get(user=self.egressa_a)
        self.assertEqual(curriculo.resumo, 'Resumo X')

    def test_experiencia_e_escolaridade_criam_editam_e_excluem(self):
        curriculo = Curriculo.objects.create(user=self.egressa_a)
        self.client.force_login(self.egressa_a)
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
        experiencia = curriculo.experiencias.get()
        response = self.client.post(
            reverse('accounts:experiencia_editar', args=[experiencia.pk]),
            {
                'empresa_nome': 'Empresa Y',
                'cargo': 'Cargo Z',
                'data_inicio': '2024-01-01',
                'data_fim': '',
                'descricao': 'Nova atividade',
            },
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            reverse('accounts:experiencia_excluir', args=[experiencia.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Experiencia.objects.filter(pk=experiencia.pk).exists())

        response = self.client.post(
            reverse('accounts:escolaridade_nova'),
            {
                'instituicao': 'Instituição',
                'curso': 'Curso',
                'nivel': 'SUPERIOR',
                'status': 'CURSANDO',
                'ano_inicio': 2024,
                'ano_conclusao': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        escolaridade = curriculo.escolaridades.get()
        response = self.client.post(
            reverse('accounts:escolaridade_excluir', args=[escolaridade.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_outra_egressa_nao_edita_experiencia(self):
        curriculo_b = Curriculo.objects.create(user=self.egressa_b)
        experiencia = Experiencia.objects.create(
            curriculo=curriculo_b,
            empresa_nome='Empresa B',
            cargo='Cargo B',
            data_inicio='2024-01-01',
        )
        self.client.force_login(self.egressa_a)
        editar = self.client.get(
            reverse('accounts:experiencia_editar', args=[experiencia.pk])
        )
        excluir = self.client.get(
            reverse('accounts:experiencia_excluir', args=[experiencia.pk])
        )
        self.assertEqual(editar.status_code, 404)
        self.assertEqual(excluir.status_code, 404)

    def test_empresa_admin_e_anonimo_bloqueados(self):
        empresa = CustomUser.objects.create_user(
            email='empresa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        admin = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='SenhaForte123!',
        )
        for user in (empresa, admin):
            self.client.force_login(user)
            self.assertEqual(
                self.client.get(reverse('accounts:curriculo')).status_code,
                403,
            )
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse('accounts:curriculo')).status_code,
            302,
        )

    def test_validacoes_e_get_or_create_sao_idempotentes(self):
        empresa = CustomUser.objects.create_user(
            email='empresa-clean@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        with self.assertRaises(ValidationError):
            Curriculo.objects.create(user=empresa)

        curriculo = Curriculo.objects.create(user=self.egressa_a)
        with self.assertRaises(ValidationError):
            Experiencia.objects.create(
                curriculo=curriculo,
                empresa_nome='Empresa',
                cargo='Cargo',
                data_inicio='2024-01-02',
                data_fim='2024-01-01',
            )
        with self.assertRaises(ValidationError):
            Escolaridade.objects.create(
                curriculo=curriculo,
                instituicao='Instituição',
                curso='Curso',
                nivel='SUPERIOR',
                status='CURSANDO',
                ano_inicio=2025,
                ano_conclusao=2024,
            )
        first = Curriculo.objects.get_or_create(user=self.egressa_a)[0]
        second = Curriculo.objects.get_or_create(user=self.egressa_a)[0]
        self.assertEqual(first.pk, second.pk)
