from datetime import timedelta

from django.contrib import messages
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from .helpers import VitrineTestCase


class FormularioVitrineTests(VitrineTestCase):
    def setUp(self):
        super().setUp()
        self.owner = self.create_user('form-owner@example.com')
        self.client.force_login(self.owner)
        self.data = {
            'nome_exibicao': 'Negócio',
            'titulo': 'Item novo',
            'descricao': 'Uma descrição',
            'categoria': 'SERVICO',
            'contato': 'contato',
            'aceito_publicar': 'on',
        }

    def test_sem_consentimento_nao_cria(self):
        response = self.client.post(reverse('vitrine:criar'), self.data | {'aceito_publicar': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.owner.produtos_servicos.count(), 0)

    def test_com_consentimento_cria_e_registra_data(self):
        before = timezone.now()
        response = self.client.post(reverse('vitrine:criar'), self.data)
        self.assertEqual(response.status_code, 302)
        item = self.owner.produtos_servicos.get()
        self.assertGreaterEqual(item.publicacao_aceita_em, before)
        self.assertLess(item.publicacao_aceita_em, timezone.now() + timedelta(seconds=1))
        self.assertTrue(any(message.level == messages.SUCCESS for message in response.wsgi_request._messages))

    def test_preco_negativo_rejeitado(self):
        response = self.client.post(reverse('vitrine:criar'), self.data | {'preco': '-1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.owner.produtos_servicos.count(), 0)

    def test_categoria_invalida_rejeitada(self):
        response = self.client.post(reverse('vitrine:criar'), self.data | {'categoria': 'OUTRA'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.owner.produtos_servicos.count(), 0)

    @override_settings(VITRINE_MAX_ITENS=2)
    def test_limite_de_itens_bloqueia_nova_criacao(self):
        self.create_item(self.owner, titulo='Um')
        self.create_item(self.owner, titulo='Dois')
        response = self.client.post(reverse('vitrine:criar'), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.owner.produtos_servicos.count(), 2)

    def test_is_ativo_false_some_publicamente(self):
        response = self.client.post(
            reverse('vitrine:criar'),
            self.data | {'is_ativo': ''},
        )
        item = self.owner.produtos_servicos.get()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(item.is_ativo)
        self.assertEqual(self.client.get(reverse('vitrine:detalhe', args=[item.pk])).status_code, 404)

    def test_edicao_atualiza_data_de_publicacao(self):
        item = self.create_item(self.owner)
        before = timezone.now()
        response = self.client.post(
            reverse('vitrine:editar', args=[item.pk]),
            self.data | {'titulo': 'Atualizado'},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.titulo, 'Atualizado')
        self.assertGreaterEqual(item.publicacao_aceita_em, before)

    def test_textos_sao_normalizados(self):
        response = self.client.post(
            reverse('vitrine:criar'),
            self.data | {
                'nome_exibicao': '  Nome  ',
                'titulo': '  Título  ',
                'contato': '  contato  ',
            },
        )
        self.assertEqual(response.status_code, 302)
        item = self.owner.produtos_servicos.get()
        self.assertEqual(item.nome_exibicao, 'Nome')
        self.assertEqual(item.titulo, 'Título')
        self.assertEqual(item.contato, 'contato')
