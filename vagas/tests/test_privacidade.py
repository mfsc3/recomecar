from django.urls import reverse

from .helpers import VagaTestCase


class PrivacidadeTests(VagaTestCase):
    def setUp(self):
        self.empresa_a = self.create_empresa('a@example.com', approved=True)
        self.empresa_b = self.create_empresa('b@example.com', approved=True)
        self.vaga_a = self.create_vaga(self.empresa_a)
        self.vaga_b = self.create_vaga(self.empresa_b)
        self.egressa = self.create_egressa()
        self.client.force_login(self.egressa)
        self.client.post(reverse('vagas:candidatar', args=[self.vaga_a.pk]))
        self.client.post(reverse('vagas:candidatar', args=[self.vaga_b.pk]))

    def test_context_contains_only_email_and_date(self):
        self.client.force_login(self.empresa_a.user)
        response = self.client.get(reverse('vagas:minha_detalhe', args=[self.vaga_a.pk]))
        candidatas = list(response.context['candidatas'])
        self.assertEqual(set(candidatas[0].keys()), {'candidata__email', 'data_candidatura'})

    def test_response_does_not_contain_first_name(self):
        self.egressa.first_name = 'NomeSecreto'
        self.egressa.save(update_fields=['first_name'])
        self.client.force_login(self.empresa_a.user)
        response = self.client.get(reverse('vagas:minha_detalhe', args=[self.vaga_a.pk]))
        self.assertNotContains(response, 'NomeSecreto')

    def test_company_a_cannot_see_company_b_vaga(self):
        self.client.force_login(self.empresa_a.user)
        response = self.client.get(reverse('vagas:minha_detalhe', args=[self.vaga_b.pk]))
        self.assertEqual(response.status_code, 404)
