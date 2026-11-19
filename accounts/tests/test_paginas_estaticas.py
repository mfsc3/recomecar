from django.test import TestCase
from django.urls import reverse


class PaginasEstaticasTests(TestCase):
    def test_sobre_retorna_200(self):
        response = self.client.get(reverse('sobre'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recomeçar é uma iniciativa')
        self.assertContains(response, 'Empreendedorismo')
        self.assertContains(response, 'Empregabilidade')
        self.assertContains(response, 'Educação e capacitação')
        self.assertContains(response, 'Nosso propósito')

    def test_faq_retorna_200(self):
        response = self.client.get(reverse('faq'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Perguntas frequentes')
        self.assertContains(response, 'Pergunta de exemplo 1')

    def test_links_no_footer_apontam_para_paginas(self):
        response = self.client.get(reverse('vagas:lista'))
        self.assertContains(response, reverse('sobre'))
        self.assertContains(response, reverse('faq'))
