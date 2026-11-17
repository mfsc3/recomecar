from django.contrib.auth import get_user_model
from django.urls import reverse

from .helpers import VagaTestCase


User = get_user_model()


class AdminAtivacaoTests(VagaTestCase):
    def setUp(self):
        self.empresa = self.create_empresa('empresa@example.com')
        self.admin = User.objects.create_superuser(
            email='super@example.com',
            password='SenhaForte123!',
        )
        self.url = reverse('admin:vagas_empresaprofile_changelist')
        self.client.force_login(self.admin)

    def aprovar(self, empresa):
        return self.client.post(
            self.url,
            {
                'action': 'aprovar_empresas',
                '_selected_action': [empresa.pk],
            },
            follow=True,
        )

    def test_aprovar_inativa_preserva_inatividade_e_avisa(self):
        self.empresa.user.is_active = False
        self.empresa.user.save(update_fields=['is_active'])

        response = self.aprovar(self.empresa)

        self.empresa.refresh_from_db()
        self.empresa.user.refresh_from_db()
        self.assertTrue(self.empresa.is_aprovada)
        self.assertFalse(self.empresa.user.is_active)
        self.assertContains(response, 'ainda não confirmaram o e-mail')

    def test_aprovar_ativa_nao_avisa_confirmacao(self):
        response = self.aprovar(self.empresa)

        self.assertNotContains(response, 'ainda não confirmaram o e-mail')

    def test_changelist_exibe_coluna_conta_ativa(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Conta ativa')
