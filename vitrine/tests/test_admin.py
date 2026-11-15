from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from .helpers import VitrineTestCase
from vitrine.admin import ProdutoServicoAdmin
from vitrine.models import ProdutoServico


class AdminVitrineTests(VitrineTestCase):
    def setUp(self):
        super().setUp()
        self.admin = ProdutoServicoAdmin(ProdutoServico, AdminSite())
        self.request = RequestFactory().get('/admin/')

    def test_acao_desativar_itens(self):
        owner = self.create_user('admin-item@example.com')
        item = self.create_item(owner)
        self.admin.desativar_itens(self.request, type(item).objects.filter(pk=item.pk))
        item.refresh_from_db()
        self.assertFalse(item.is_ativo)

    def test_nao_permite_adicionar(self):
        self.assertFalse(self.admin.has_add_permission(self.request))

    def test_campos_readonly(self):
        self.assertEqual(
            set(self.admin.readonly_fields),
            {
                'owner',
                'imagem',
                'publicacao_aceita_em',
                'criado_em',
                'atualizado_em',
            },
        )

    def test_list_display(self):
        self.assertEqual(
            self.admin.list_display,
            ('titulo', 'nome_exibicao', 'categoria', 'is_ativo', 'owner', 'criado_em'),
        )

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('categoria', 'is_ativo'))

    def test_search_fields(self):
        self.assertIn('owner__email', self.admin.search_fields)
