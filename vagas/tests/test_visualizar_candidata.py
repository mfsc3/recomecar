from django.test import TestCase
from django.urls import reverse

from accounts.models import Curriculo, CustomUser
from vagas.models import Candidatura, EmpresaProfile, Vaga


class VisualizarCandidataTests(TestCase):
    def setUp(self):
        self.egressa = CustomUser.objects.create_user(
            email='egressa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        Curriculo.objects.create(user=self.egressa, resumo='Resumo')
        self.empresa_a_user = CustomUser.objects.create_user(
            email='empresa-a@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        self.empresa_a = EmpresaProfile.objects.create(
            user=self.empresa_a_user,
            cnpj='11222333000181',
            razao_social='Empresa A',
            is_aprovada=True,
        )
        self.empresa_b_user = CustomUser.objects.create_user(
            email='empresa-b@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        self.empresa_b = EmpresaProfile.objects.create(
            user=self.empresa_b_user,
            cnpj='22333444000182',
            razao_social='Empresa B',
            is_aprovada=True,
        )
        self.vaga_a = Vaga.objects.create(
            empresa=self.empresa_a,
            titulo='Vaga A',
            descricao='Descrição',
            requisitos='Requisitos',
        )
        self.vaga_a2 = Vaga.objects.create(
            empresa=self.empresa_a,
            titulo='Vaga A2',
            descricao='Descrição',
            requisitos='Requisitos',
        )
        self.candidatura = Candidatura.objects.create(
            vaga=self.vaga_a,
            candidata=self.egressa,
            curriculo_snapshot={
                'resumo': 'Resumo',
                'habilidades': 'Python',
                'experiencias': [
                    {
                        'empresa_nome': 'Empresa Y',
                        'cargo': 'Cargo X',
                        'data_inicio': '2024-01-01',
                        'data_fim': None,
                        'descricao': 'Atividades',
                    }
                ],
                'escolaridades': [],
            },
        )

    def test_empresa_dona_ve_snapshot(self):
        self.client.force_login(self.empresa_a_user)
        response = self.client.get(
            reverse(
                'vagas:candidata_curriculo',
                args=[self.vaga_a.pk, self.candidatura.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cargo X')
        self.assertContains(response, 'Empresa Y')

    def test_outras_empresas_e_vaga_inconsistente_retorna_404(self):
        self.client.force_login(self.empresa_b_user)
        response = self.client.get(
            reverse(
                'vagas:candidata_curriculo',
                args=[self.vaga_a.pk, self.candidatura.pk],
            )
        )
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.empresa_a_user)
        response = self.client.get(
            reverse(
                'vagas:candidata_curriculo',
                args=[self.vaga_a2.pk, self.candidatura.pk],
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_snapshot_nulo_e_empresa_revogada(self):
        self.candidatura.curriculo_snapshot = None
        self.candidatura.save()
        self.empresa_a.is_aprovada = False
        self.empresa_a.save()
        self.client.force_login(self.empresa_a_user)
        response = self.client.get(
            reverse(
                'vagas:candidata_curriculo',
                args=[self.vaga_a.pk, self.candidatura.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Currículo não disponível')

    def test_egressa_e_admin_bloqueados_em_candidata_curriculo(self):
        admin = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='SenhaForte123!',
        )
        for user in (self.egressa, admin):
            self.client.force_login(user)
            self.assertEqual(
                self.client.get(
                    reverse(
                        'vagas:candidata_curriculo',
                        args=[self.vaga_a.pk, self.candidatura.pk],
                    )
                ).status_code,
                403,
            )

    def test_empresa_sem_perfil_bloqueada_em_empresa_editar(self):
        user = CustomUser.objects.create_user(
            email='sem-perfil@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        self.client.force_login(user)
        self.assertEqual(
            self.client.get(reverse('vagas:empresa_editar')).status_code,
            403,
        )

    def test_anonimo_redirecionado_em_candidata_curriculo(self):
        response = self.client.get(
            reverse(
                'vagas:candidata_curriculo',
                args=[self.vaga_a.pk, self.candidatura.pk],
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_admin_bloqueado_em_empresa_editar(self):
        admin = CustomUser.objects.create_superuser(
            email='admin-empresa@example.com',
            password='SenhaForte123!',
        )
        self.client.force_login(admin)
        self.assertEqual(
            self.client.get(reverse('vagas:empresa_editar')).status_code,
            403,
        )
