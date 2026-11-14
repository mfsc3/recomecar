from django.urls import reverse

from .helpers import VagaTestCase


class PublicoTests(VagaTestCase):
    def setUp(self):
        self.aprovada = self.create_empresa('aprovada@example.com', approved=True)
        self.pendente = self.create_empresa('pendente@example.com', approved=False)

    def test_anonymous_can_access_list(self):
        self.assertEqual(self.client.get(reverse('vagas:lista')).status_code, 200)

    def test_only_active_vagas_from_approved_companies_are_listed(self):
        visible = self.create_vaga(self.aprovada, 'Visível')
        self.create_vaga(self.aprovada, 'Inativa', ativa=False)
        self.create_vaga(self.pendente, 'Pendente')
        response = self.client.get(reverse('vagas:lista'))
        self.assertContains(response, visible.titulo)
        self.assertNotContains(response, 'Inativa')
        self.assertNotContains(response, 'Pendente')

    def test_inactive_and_pending_detail_are_404(self):
        inactive = self.create_vaga(self.aprovada, 'Inativa', ativa=False)
        pending = self.create_vaga(self.pendente, 'Pendente')
        self.assertEqual(self.client.get(reverse('vagas:detalhe_publica', args=[inactive.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('vagas:detalhe_publica', args=[pending.pk])).status_code, 404)

    def test_public_page_does_not_show_private_fields(self):
        vaga = self.create_vaga(self.aprovada)
        response = self.client.get(reverse('vagas:detalhe_publica', args=[vaga.pk]))
        self.assertNotContains(response, self.aprovada.cnpj)
        self.assertNotContains(response, self.aprovada.user.email)

    def test_pagination_has_two_pages_for_eleven_vagas(self):
        for index in range(11):
            self.create_vaga(self.aprovada, f'Vaga {index}')
        first = self.client.get(reverse('vagas:lista'))
        second = self.client.get(f'{reverse("vagas:lista")}?page=2')
        self.assertTrue(first.context['is_paginated'])
        self.assertEqual(first.context['page_obj'].paginator.num_pages, 2)
        self.assertEqual(second.status_code, 200)

    def test_title_is_escaped(self):
        vaga = self.create_vaga(self.aprovada, '<script>alert(1)</script>')
        response = self.client.get(reverse('vagas:detalhe_publica', args=[vaga.pk]))
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
