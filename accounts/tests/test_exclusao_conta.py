from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from allauth.account.models import EmailAddress

from accounts.models import Curriculo, CustomUser, Escolaridade, Experiencia
from vagas.models import Candidatura, EmpresaProfile, Vaga


class ExclusaoContaTests(TestCase):
    def setUp(self):
        self.egressa = CustomUser.objects.create_user(
            email='egressa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        EmailAddress.objects.create(
            user=self.egressa,
            email=self.egressa.email,
            primary=True,
            verified=True,
        )
        self.curriculo = Curriculo.objects.create(
            user=self.egressa,
            resumo='Resumo',
            habilidades='Python',
        )
        self.experiencia = Experiencia.objects.create(
            curriculo=self.curriculo,
            empresa_nome='Empresa',
            cargo='Cargo',
            data_inicio='2024-01-01',
        )
        self.escolaridade = Escolaridade.objects.create(
            curriculo=self.curriculo,
            instituicao='Instituição',
            curso='Curso',
            nivel='SUPERIOR',
            status='CURSANDO',
        )

        self.outra_egressa = CustomUser.objects.create_user(
            email='outra-egressa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        Curriculo.objects.create(user=self.outra_egressa)

        empresa_user = CustomUser.objects.create_user(
            email='empresa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        self.empresa = EmpresaProfile.objects.create(
            user=empresa_user,
            cnpj='11222333000181',
            razao_social='Empresa A',
            is_aprovada=True,
        )
        self.vaga = Vaga.objects.create(
            empresa=self.empresa,
            titulo='Analista',
            descricao='Descricao',
            requisitos='Requisitos',
        )
        self.candidatura = Candidatura.objects.create(
            vaga=self.vaga,
            candidata=self.egressa,
            curriculo_snapshot={'resumo': 'Resumo'},
        )

        outra_empresa_user = CustomUser.objects.create_user(
            email='outra-empresa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        self.outra_empresa = EmpresaProfile.objects.create(
            user=outra_empresa_user,
            cnpj='22333444000182',
            razao_social='Empresa B',
            is_aprovada=True,
        )
        self.outra_vaga = Vaga.objects.create(
            empresa=self.outra_empresa,
            titulo='Assistente',
            descricao='Descricao',
            requisitos='Requisitos',
        )

    def test_confirmacao_errada_nao_exclui(self):
        self.client.force_login(self.egressa)
        for confirmacao in ('excluir', '', 'EXCLUIR '):
            response = self.client.post(
                reverse('accounts:excluir_conta'),
                {'confirmacao': confirmacao},
            )
            self.assertRedirects(response, reverse('accounts:excluir_conta'))
            self.assertTrue(
                CustomUser.objects.filter(pk=self.egressa.pk).exists()
            )

    def test_excluir_egressa_sem_orfaos(self):
        self.client.force_login(self.egressa)
        response = self.client.post(
            reverse('accounts:excluir_conta'),
            {'confirmacao': 'EXCLUIR'},
        )
        self.assertRedirects(
            response,
            reverse('vagas:lista'),
            fetch_redirect_response=False,
        )
        pk = self.egressa.pk
        self.assertFalse(CustomUser.objects.filter(pk=pk).exists())
        self.assertFalse(Curriculo.objects.filter(user_id=pk).exists())
        self.assertFalse(
            Experiencia.objects.filter(curriculo__user_id=pk).exists()
        )
        self.assertFalse(
            Escolaridade.objects.filter(curriculo__user_id=pk).exists()
        )
        self.assertFalse(Candidatura.objects.filter(candidata_id=pk).exists())

    def test_excluir_egressa_nao_afeta_empresa_nem_outras_candidaturas(self):
        outra_candidatura = Candidatura.objects.create(
            vaga=self.outra_vaga,
            candidata=self.outra_egressa,
            curriculo_snapshot={'resumo': 'Outro currículo'},
        )
        self.client.force_login(self.egressa)
        self.client.post(
            reverse('accounts:excluir_conta'),
            {'confirmacao': 'EXCLUIR'},
        )
        self.assertTrue(CustomUser.objects.filter(pk=self.outra_egressa.pk).exists())
        self.assertTrue(
            CustomUser.objects.filter(pk=self.empresa.user_id).exists()
        )
        self.assertTrue(Candidatura.objects.filter(pk=outra_candidatura.pk).exists())

    def test_excluir_empresa_deleta_vagas_e_candidaturas_recebidas(self):
        self.client.force_login(self.empresa.user)
        pk = self.empresa.user_id
        response = self.client.post(
            reverse('accounts:excluir_conta'),
            {'confirmacao': 'EXCLUIR'},
        )
        self.assertRedirects(
            response,
            reverse('vagas:lista'),
            fetch_redirect_response=False,
        )
        self.assertFalse(CustomUser.objects.filter(pk=pk).exists())
        self.assertFalse(EmpresaProfile.objects.filter(user_id=pk).exists())
        self.assertFalse(Vaga.objects.filter(empresa__user_id=pk).exists())
        self.assertFalse(
            Candidatura.objects.filter(vaga__empresa__user_id=pk).exists()
        )

    def test_excluir_empresa_nao_afeta_outras_empresas(self):
        self.client.force_login(self.empresa.user)
        self.client.post(
            reverse('accounts:excluir_conta'),
            {'confirmacao': 'EXCLUIR'},
        )
        self.assertTrue(
            CustomUser.objects.filter(pk=self.outra_empresa.user_id).exists()
        )
        self.assertTrue(
            EmpresaProfile.objects.filter(pk=self.outra_empresa.pk).exists()
        )
        self.assertTrue(CustomUser.objects.filter(pk=self.egressa.pk).exists())
        self.assertTrue(Curriculo.objects.filter(user_id=self.egressa.pk).exists())
        self.assertFalse(Candidatura.objects.filter(candidata_id=self.egressa.pk).exists())

    def test_admin_nao_pode_excluir_pela_view(self):
        admin = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='SenhaForte123!',
        )
        self.client.force_login(admin)
        self.assertEqual(
            self.client.get(reverse('accounts:excluir_conta')).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('accounts:excluir_conta'),
                {'confirmacao': 'EXCLUIR'},
            ).status_code,
            403,
        )

    def test_anonimo_redirecionado_para_login(self):
        response = self.client.get(reverse('accounts:excluir_conta'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_excluir_falha_faz_rollback_e_mantem_sessao(self):
        self.client.force_login(self.egressa)
        with patch.object(
            CustomUser,
            'delete',
            side_effect=Exception('boom'),
        ):
            response = self.client.post(
                reverse('accounts:excluir_conta'),
                {'confirmacao': 'EXCLUIR'},
            )
        self.assertRedirects(
            response,
            reverse('accounts:painel'),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            CustomUser.objects.filter(pk=self.egressa.pk).exists()
        )
        self.assertEqual(
            self.client.get(reverse('accounts:painel')).status_code,
            200,
        )
