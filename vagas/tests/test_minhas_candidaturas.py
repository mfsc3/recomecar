from django.test import TestCase
from django.urls import reverse

from accounts.models import Curriculo, CustomUser
from vagas.models import Candidatura, EmpresaProfile, Vaga


class MinhasCandidaturasTests(TestCase):
    def setUp(self):
        self.egressa = CustomUser.objects.create_user(
            email='a@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        Curriculo.objects.create(
            user=self.egressa,
            resumo='Resumo original',
            habilidades='Python',
        )
        self.outra_egressa = CustomUser.objects.create_user(
            email='b@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        Curriculo.objects.create(user=self.outra_egressa)
        empresa_user = CustomUser.objects.create_user(
            email='empresa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        empresa = EmpresaProfile.objects.create(
            user=empresa_user,
            cnpj='11222333000181',
            razao_social='Empresa A',
            is_aprovada=True,
        )
        vaga = Vaga.objects.create(
            empresa=empresa,
            titulo='Analista',
            descricao='Descricao',
            requisitos='Requisitos',
        )
        self.candidatura = Candidatura.objects.create(
            vaga=vaga,
            candidata=self.egressa,
            curriculo_snapshot={
                'resumo': 'Resumo original',
                'habilidades': 'Python',
                'experiencias': [],
                'escolaridades': [],
            },
        )
        outra_vaga = Vaga.objects.create(
            empresa=empresa,
            titulo='Assistente',
            descricao='Descricao',
            requisitos='Requisitos',
        )
        self.outra_candidatura = Candidatura.objects.create(
            vaga=outra_vaga,
            candidata=self.outra_egressa,
            curriculo_snapshot={'resumo': 'Outro currículo'},
        )

    def test_egressa_ve_somente_suas_candidaturas(self):
        self.client.force_login(self.egressa)
        response = self.client.get(reverse('vagas:minhas_candidaturas'))
        self.assertEqual(response.status_code, 200)
        candidaturas = list(response.context['candidaturas'])
        self.assertEqual(candidaturas, [self.candidatura])

    def test_egressa_sem_candidaturas_ve_estado_vazio(self):
        nova = CustomUser.objects.create_user(
            email='sem-candidatura@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        Curriculo.objects.create(user=nova)
        self.client.force_login(nova)
        response = self.client.get(reverse('vagas:minhas_candidaturas'))
        self.assertContains(response, 'Você ainda não se candidatou a nenhuma vaga.')

    def test_meu_snapshot_mostra_json_original(self):
        self.client.force_login(self.egressa)
        response = self.client.get(
            reverse('vagas:meu_snapshot', args=[self.candidatura.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resumo original')
        self.assertContains(response, 'Voltar')

    def test_egressa_nao_ve_snapshot_de_outra(self):
        self.client.force_login(self.egressa)
        response = self.client.get(
            reverse('vagas:meu_snapshot', args=[self.outra_candidatura.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_empresa_admin_anonimo_bloqueados_em_minhas_candidaturas(self):
        empresa = CustomUser.objects.get(role=CustomUser.Role.EMPRESA)
        admin = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='SenhaForte123!',
        )

        for user in (empresa, admin):
            self.client.force_login(user)
            self.assertEqual(
                self.client.get(reverse('vagas:minhas_candidaturas')).status_code,
                403,
            )
            self.assertEqual(
                self.client.get(
                    reverse('vagas:meu_snapshot', args=[self.candidatura.pk])
                ).status_code,
                403,
            )

        self.client.logout()
        for url in (
            reverse('vagas:minhas_candidaturas'),
            reverse('vagas:meu_snapshot', args=[self.candidatura.pk]),
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response['Location'])
