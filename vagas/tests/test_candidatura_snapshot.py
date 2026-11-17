from django.test import TestCase
from django.urls import reverse

from accounts.models import Curriculo, Experiencia
from vagas.models import Candidatura, EmpresaProfile, Vaga
from accounts.models import CustomUser


class CandidaturaSnapshotTests(TestCase):
    def setUp(self):
        self.egressa = CustomUser.objects.create_user(
            email='egressa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
        empresa_user = CustomUser.objects.create_user(
            email='empresa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        self.empresa = EmpresaProfile.objects.create(
            user=empresa_user,
            cnpj='11222333000181',
            razao_social='Empresa',
            is_aprovada=True,
        )
        self.vaga = Vaga.objects.create(
            empresa=self.empresa,
            titulo='Vaga',
            descricao='Descrição',
            requisitos='Requisitos',
        )

    def test_sem_curriculo_redireciona_e_nao_candidata(self):
        self.client.force_login(self.egressa)
        response = self.client.post(
            reverse('vagas:candidatar', args=[self.vaga.pk]),
            follow=True,
        )
        self.assertRedirects(response, reverse('accounts:curriculo'))
        self.assertContains(response, 'preencha seu currículo')
        self.assertEqual(Candidatura.objects.count(), 0)

    def test_snapshot_e_immutavel_e_sem_pii(self):
        curriculo = Curriculo.objects.create(
            user=self.egressa,
            resumo='Resumo original',
            habilidades='Python',
        )
        experiencia = Experiencia.objects.create(
            curriculo=curriculo,
            empresa_nome='Empresa Y',
            cargo='Cargo X',
            data_inicio='2024-01-01',
        )
        self.client.force_login(self.egressa)
        self.client.post(reverse('vagas:candidatar', args=[self.vaga.pk]))
        candidatura = Candidatura.objects.get()
        snapshot = candidatura.curriculo_snapshot
        self.assertIn('Resumo original', snapshot['resumo'])
        self.assertIn('Cargo X', str(snapshot))
        self.assertNotIn('email', snapshot)
        self.assertNotIn('candidata', snapshot)
        self.assertNotIn('user_id', snapshot)

        experiencia.cargo = 'Cargo Editado'
        experiencia.save()
        curriculo.resumo = 'Resumo editado'
        curriculo.save()
        candidatura.refresh_from_db()
        self.assertIn('Resumo original', candidatura.curriculo_snapshot['resumo'])
        self.assertIn(
            'Cargo X',
            candidatura.curriculo_snapshot['experiencias'][0]['cargo'],
        )

        response = self.client.post(
            reverse('vagas:candidatar', args=[self.vaga.pk])
        )
        self.assertEqual(Candidatura.objects.count(), 1)
        candidatura.refresh_from_db()
        self.assertIn('Resumo original', candidatura.curriculo_snapshot['resumo'])
