from django.urls import reverse

from .helpers import VitrineTestCase


class IdorVitrineTests(VitrineTestCase):
    def setUp(self):
        super().setUp()
        self.a = self.create_user('a@example.com')
        self.b = self.create_user('b@example.com')
        self.item = self.create_item(self.a)
        self.client.force_login(self.b)

    def test_b_nao_edita_get(self):
        self.assertEqual(self.client.get(reverse('vitrine:editar', args=[self.item.pk])).status_code, 404)

    def test_b_nao_edita_post(self):
        response = self.client.post(reverse('vitrine:editar', args=[self.item.pk]), {})
        self.assertEqual(response.status_code, 404)
        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Bolos artesanais')

    def test_b_nao_exclui_get(self):
        self.assertEqual(self.client.get(reverse('vitrine:excluir', args=[self.item.pk])).status_code, 404)

    def test_b_nao_exclui_post(self):
        response = self.client.post(reverse('vitrine:excluir', args=[self.item.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(type(self.item).objects.filter(pk=self.item.pk).exists())

    def test_pk_inexistente_editar(self):
        self.assertEqual(self.client.get(reverse('vitrine:editar', args=[999])).status_code, 404)

    def test_pk_inexistente_excluir(self):
        self.assertEqual(self.client.get(reverse('vitrine:excluir', args=[999])).status_code, 404)

    def test_get_excluir_nao_apaga(self):
        self.client.force_login(self.a)
        response = self.client.get(reverse('vitrine:excluir', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(type(self.item).objects.filter(pk=self.item.pk).exists())

    def test_inativo_aparece_na_minhas(self):
        self.client.force_login(self.a)
        self.item.is_ativo = False
        self.item.save()
        response = self.client.get(reverse('vitrine:minha'))
        self.assertContains(response, self.item.titulo)

    def test_inativo_nao_aparece_publicamente(self):
        self.item.is_ativo = False
        self.item.save()
        self.assertEqual(self.client.get(reverse('vitrine:detalhe', args=[self.item.pk])).status_code, 404)
