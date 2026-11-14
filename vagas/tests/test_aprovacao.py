from django.urls import reverse

from accounts.models import CustomUser
from vagas.models import EmpresaProfile, Vaga

from .helpers import VagaTestCase


class AprovacaoTests(VagaTestCase):
    def setUp(self):
        self.empresa = self.create_empresa('empresa@example.com')

    def test_new_empresa_starts_unapproved(self):
        self.assertFalse(self.empresa.is_aprovada)

    def test_public_registration_cannot_set_approval(self):
        response = self.client.post(
            reverse('accounts:cadastro_empresa'),
            {
                'first_name': 'Responsável',
                'email': 'nova@example.com',
                'password1': 'SenhaForte123!',
                'password2': 'SenhaForte123!',
                'aceitou_termo': 'on',
                'razao_social': 'Nova Empresa',
                'cnpj': '12.345.678/0001-95',
                'is_aprovada': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        profile = EmpresaProfile.objects.get(user__email='nova@example.com')
        self.assertFalse(profile.is_aprovada)

    def test_unapproved_company_cannot_create_or_edit(self):
        vaga = self.create_vaga(self.empresa)
        self.client.force_login(self.empresa.user)
        create_response = self.client.get(reverse('vagas:criar'))
        self.assertRedirects(create_response, reverse('accounts:painel'))
        edit_response = self.client.post(
            reverse('vagas:editar', args=[vaga.pk]),
            {'titulo': 'Tentativa', 'descricao': 'x', 'requisitos': 'y', 'ativa': 'on'},
        )
        self.assertRedirects(edit_response, reverse('accounts:painel'))
        vaga.refresh_from_db()
        self.assertEqual(vaga.titulo, 'Vaga de teste')

    def test_approved_company_creates_with_backend_owner(self):
        self.empresa.is_aprovada = True
        self.empresa.save()
        other = self.create_empresa('other@example.com', approved=True)
        self.client.force_login(self.empresa.user)
        response = self.client.post(
            reverse('vagas:criar'),
            {
                'titulo': 'Nova vaga',
                'descricao': 'Atividades',
                'requisitos': 'Competências',
                'ativa': 'on',
                'empresa': other.pk,
            },
        )
        self.assertRedirects(response, reverse('vagas:minhas'))
        vaga = Vaga.objects.get(titulo='Nova vaga')
        self.assertEqual(vaga.empresa, self.empresa)

    def test_unapproved_company_can_list_view_and_delete_own_vaga(self):
        vaga = self.create_vaga(self.empresa)
        self.client.force_login(self.empresa.user)
        self.assertEqual(self.client.get(reverse('vagas:minhas')).status_code, 200)
        self.assertEqual(self.client.get(reverse('vagas:minha_detalhe', args=[vaga.pk])).status_code, 200)
        response = self.client.post(
            reverse('vagas:excluir', args=[vaga.pk]),
            follow=True,
        )
        self.assertFalse(Vaga.objects.filter(pk=vaga.pk).exists())
        self.assertContains(response, 'Vaga excluída com sucesso.')

    def test_revoking_approval_hides_public_vaga_and_blocks_application(self):
        self.empresa.is_aprovada = True
        self.empresa.save()
        vaga = self.create_vaga(self.empresa)
        egressa = self.create_egressa()
        self.assertEqual(self.client.get(reverse('vagas:lista')).status_code, 200)
        self.empresa.is_aprovada = False
        self.empresa.save()
        response = self.client.get(reverse('vagas:lista'))
        self.assertNotContains(response, vaga.titulo)
        self.assertEqual(self.client.get(reverse('vagas:detalhe_publica', args=[vaga.pk])).status_code, 404)
        self.client.force_login(egressa)
        self.assertEqual(self.client.post(reverse('vagas:candidatar', args=[vaga.pk])).status_code, 404)

    def test_admin_can_approve_and_revoke(self):
        admin_user = CustomUser.objects.create_superuser(
            email='super@example.com',
            password='SenhaForte123!',
        )
        self.client.force_login(admin_user)
        url = reverse('admin:vagas_empresaprofile_changelist')
        response = self.client.post(url, {
            'action': 'aprovar_empresas',
            '_selected_action': [self.empresa.pk],
        })
        self.assertEqual(response.status_code, 302)
        self.empresa.refresh_from_db()
        self.assertTrue(self.empresa.is_aprovada)
        response = self.client.post(url, {
            'action': 'revogar_aprovacao',
            '_selected_action': [self.empresa.pk],
        })
        self.assertEqual(response.status_code, 302)
        self.empresa.refresh_from_db()
        self.assertFalse(self.empresa.is_aprovada)
