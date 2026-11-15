from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError

from accounts.models import CustomUser

from .helpers import VitrineTestCase


class PermissoesVitrineTests(VitrineTestCase):
    def setUp(self):
        super().setUp()
        self.egressa = self.create_user('egressa@example.com')
        self.empresa = self.create_user(
            'empresa@example.com',
            role=CustomUser.Role.EMPRESA,
        )
        self.admin = self.create_user(
            'admin@example.com',
            role=CustomUser.Role.ADMIN,
        )
        self.form_data = {
            'nome_exibicao': 'Ateliê',
            'titulo': 'Produto',
            'descricao': 'Descrição',
            'categoria': 'PRODUTO',
            'contato': 'contato',
            'aceito_publicar': 'on',
        }

    def test_anonimo_criar_redireciona(self):
        response = self.client.get(reverse('vitrine:criar'))
        self.assertRedirects(response, f'{reverse("accounts:login")}?next=/vitrine/minha/novo/')

    def test_anonimo_minha_redireciona(self):
        response = self.client.get(reverse('vitrine:minha'))
        self.assertRedirects(response, f'{reverse("accounts:login")}?next=/vitrine/minha/')

    def test_anonimo_editar_redireciona(self):
        response = self.client.get(reverse('vitrine:editar', args=[1]))
        self.assertRedirects(response, f'{reverse("accounts:login")}?next=/vitrine/minha/1/editar/')

    def test_anonimo_excluir_redireciona(self):
        response = self.client.get(reverse('vitrine:excluir', args=[1]))
        self.assertRedirects(response, f'{reverse("accounts:login")}?next=/vitrine/minha/1/excluir/')

    def test_empresa_criar_403(self):
        self.client.force_login(self.empresa)
        self.assertEqual(self.client.get(reverse('vitrine:criar')).status_code, 403)

    def test_empresa_minha_403(self):
        self.client.force_login(self.empresa)
        self.assertEqual(self.client.get(reverse('vitrine:minha')).status_code, 403)

    def test_empresa_editar_403(self):
        self.client.force_login(self.empresa)
        self.assertEqual(self.client.get(reverse('vitrine:editar', args=[1])).status_code, 403)

    def test_empresa_excluir_403(self):
        self.client.force_login(self.empresa)
        self.assertEqual(self.client.get(reverse('vitrine:excluir', args=[1])).status_code, 403)

    def test_admin_criar_403(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('vitrine:criar')).status_code, 403)

    def test_admin_minha_403(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('vitrine:minha')).status_code, 403)

    def test_admin_editar_403(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('vitrine:editar', args=[1])).status_code, 403)

    def test_admin_excluir_403(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('vitrine:excluir', args=[1])).status_code, 403)

    def test_egressa_acessa_minha(self):
        self.client.force_login(self.egressa)
        self.assertEqual(self.client.get(reverse('vitrine:minha')).status_code, 200)

    def test_owner_do_post_e_ignorado(self):
        outra = self.create_user('outra@example.com')
        self.client.force_login(self.egressa)
        response = self.client.post(
            reverse('vitrine:criar'),
            {**self.form_data, 'owner': outra.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.egressa.produtos_servicos.count(), 1)
        self.assertEqual(self.egressa.produtos_servicos.first().owner, self.egressa)

    def test_publicacao_do_post_e_ignorada(self):
        self.client.force_login(self.egressa)
        self.client.post(
            reverse('vitrine:criar'),
            {**self.form_data, 'publicacao_aceita_em': '2000-01-01'},
        )
        item = self.egressa.produtos_servicos.get()
        self.assertIsNotNone(item.publicacao_aceita_em)
        self.assertGreater(item.publicacao_aceita_em, timezone.datetime(2020, 1, 1, tzinfo=timezone.get_current_timezone()))

    def test_modelo_rejeita_empresa(self):
        with self.assertRaisesMessage(
            ValidationError,
            'Somente contas de egressas podem ter itens na vitrine.',
        ):
            self.create_item(self.empresa)
