from django.urls import reverse

from accounts.models import CustomUser
from vagas.models import Candidatura

from .helpers import VagaTestCase


class CandidaturaTests(VagaTestCase):
    def setUp(self):
        self.empresa = self.create_empresa('empresa@example.com', approved=True)
        self.vaga = self.create_vaga(self.empresa)
        self.egressa = self.create_egressa()

    def test_egressa_can_apply(self):
        self.client.force_login(self.egressa)
        response = self.client.post(reverse('vagas:candidatar', args=[self.vaga.pk]))
        self.assertRedirects(response, reverse('vagas:detalhe_publica', args=[self.vaga.pk]))
        self.assertEqual(Candidatura.objects.count(), 1)

    def test_duplicate_application_is_friendly(self):
        self.client.force_login(self.egressa)
        self.client.post(reverse('vagas:candidatar', args=[self.vaga.pk]))
        response = self.client.post(reverse('vagas:candidatar', args=[self.vaga.pk]), follow=True)
        self.assertEqual(Candidatura.objects.count(), 1)
        self.assertContains(response, 'Você já se candidatou a esta vaga.')

    def test_company_and_admin_are_forbidden(self):
        self.client.raise_request_exception = False
        admin_user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='SenhaForte123!',
        )
        for user in (self.empresa.user, admin_user):
            self.client.force_login(user)
            self.assertEqual(self.client.post(reverse('vagas:candidatar', args=[self.vaga.pk])).status_code, 403)

    def test_anonymous_is_redirected(self):
        response = self.client.post(reverse('vagas:candidatar', args=[self.vaga.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/?next=', response['Location'])

    def test_get_is_not_allowed(self):
        self.client.force_login(self.egressa)
        self.assertEqual(self.client.get(reverse('vagas:candidatar', args=[self.vaga.pk])).status_code, 405)

    def test_inactive_or_pending_vaga_is_not_available(self):
        self.client.force_login(self.egressa)
        self.vaga.ativa = False
        self.vaga.save()
        self.assertEqual(self.client.post(reverse('vagas:candidatar', args=[self.vaga.pk])).status_code, 404)
        self.vaga.ativa = True
        self.vaga.save()
        self.empresa.is_aprovada = False
        self.empresa.save()
        self.assertEqual(self.client.post(reverse('vagas:candidatar', args=[self.vaga.pk])).status_code, 404)

    def test_post_candidate_id_is_ignored(self):
        other = self.create_egressa('other@example.com')
        self.client.force_login(self.egressa)
        self.client.post(
            reverse('vagas:candidatar', args=[self.vaga.pk]),
            {'candidata': other.pk},
        )
        candidatura = Candidatura.objects.get()
        self.assertEqual(candidatura.candidata, self.egressa)

    def test_email_sharing_notice_is_present(self):
        self.client.force_login(self.egressa)
        response = self.client.get(reverse('vagas:detalhe_publica', args=[self.vaga.pk]))
        self.assertContains(response, 'seu e-mail será compartilhado com a empresa responsável')
