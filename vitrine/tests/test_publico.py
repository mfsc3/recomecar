from pathlib import Path

from django.urls import reverse

from .helpers import VitrineTestCase


class PublicoVitrineTests(VitrineTestCase):
    def setUp(self):
        super().setUp()
        self.owner = self.create_user('public-owner@example.com')
        self.owner.first_name = 'Zuleica'
        self.owner.last_name = 'Quintanilha'
        self.owner.save()
        self.item = self.create_item(
            self.owner,
            titulo='Serviço público',
            descricao='Descrição pública',
            contato='Contato público',
        )

    def test_anonimo_ve_lista(self):
        response = self.client.get(reverse('vitrine:lista'))
        self.assertEqual(response.status_code, 200)

    def test_anonimo_ve_detalhe(self):
        response = self.client.get(reverse('vitrine:detalhe', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_lista_mostra_apenas_ativos(self):
        self.create_item(self.owner, titulo='Inativo', is_ativo=False)
        response = self.client.get(reverse('vitrine:lista'))
        self.assertContains(response, 'Serviço público')
        self.assertNotContains(response, 'Inativo')

    def test_detalhe_exige_item_ativo(self):
        self.item.is_ativo = False
        self.item.save()
        self.assertEqual(self.client.get(reverse('vitrine:detalhe', args=[self.item.pk])).status_code, 404)

    def test_dono_inativo_some_da_lista(self):
        self.owner.is_active = False
        self.owner.save()
        response = self.client.get(reverse('vitrine:lista'))
        self.assertNotContains(response, 'Serviço público')

    def test_dono_inativo_detalhe_404(self):
        self.owner.is_active = False
        self.owner.save()
        self.assertEqual(self.client.get(reverse('vitrine:detalhe', args=[self.item.pk])).status_code, 404)

    def test_paginacao(self):
        for number in range(12):
            self.create_item(self.owner, titulo=f'Item {number}')
        response = self.client.get(reverse('vitrine:lista'))
        self.assertEqual(response.context['paginator'].count, 13)
        self.assertEqual(response.context['paginator'].num_pages, 2)

    def test_lista_nao_expoe_dados_do_dono(self):
        response = self.client.get(reverse('vitrine:lista'))
        self.assertNotContains(response, self.owner.email)
        self.assertNotContains(response, self.owner.first_name)
        self.assertNotContains(response, self.owner.last_name)

    def test_detalhe_nao_expoe_dados_do_dono(self):
        response = self.client.get(reverse('vitrine:detalhe', args=[self.item.pk]))
        self.assertNotContains(response, self.owner.email)
        self.assertNotContains(response, self.owner.first_name)
        self.assertNotContains(response, self.owner.last_name)

    def test_detalhe_contem_nome_e_contato(self):
        response = self.client.get(reverse('vitrine:detalhe', args=[self.item.pk]))
        self.assertContains(response, self.item.nome_exibicao)
        self.assertContains(response, self.item.contato)

    def test_dados_do_usuario_sao_escapados(self):
        self.item.titulo = '<script>alert(1)</script>'
        self.item.descricao = '<script>descricao</script>'
        self.item.contato = '<script>contato</script>'
        self.item.save()
        response = self.client.get(reverse('vitrine:detalhe', args=[self.item.pk]))
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_contato_nao_vira_link(self):
        response = self.client.get(reverse('vitrine:detalhe', args=[self.item.pk]))
        self.assertContains(response, self.item.contato)
        self.assertNotContains(response, '<a href="mailto:')
        self.assertNotContains(response, '<a href="https://')

    def test_templates_publicos_nao_contem_termo_de_papel(self):
        root = Path(__file__).resolve().parents[2]
        for name in ('lista.html', 'detalhe.html'):
            source = (root / 'templates' / 'vitrine' / name).read_text(
                encoding='utf-8'
            )
            self.assertNotIn('egressa', source.lower())
