from django.urls import reverse

from accounts.models import CustomUser
from vagas.models import Vaga

from .helpers import VagaTestCase


class IdorTests(VagaTestCase):
    def setUp(self):
        self.empresa_a = self.create_empresa('a@example.com', approved=True)
        self.empresa_b = self.create_empresa('b@example.com', approved=True)
        self.vaga_a = self.create_vaga(self.empresa_a)
        self.user_b = self.empresa_b.user
        self.egressa = self.create_egressa()
        self.admin = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='SenhaForte123!',
        )

    def test_other_company_get_detail_is_404(self):
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('vagas:minha_detalhe', args=[self.vaga_a.pk]))
        self.assertEqual(response.status_code, 404)

    def test_other_company_cannot_get_or_post_edit(self):
        self.client.force_login(self.user_b)
        url = reverse('vagas:editar', args=[self.vaga_a.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'titulo': 'Alterada'}).status_code, 404)
        self.vaga_a.refresh_from_db()
        self.assertEqual(self.vaga_a.titulo, 'Vaga de teste')

    def test_other_company_cannot_get_or_post_delete(self):
        self.client.force_login(self.user_b)
        url = reverse('vagas:excluir', args=[self.vaga_a.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(Vaga.objects.filter(pk=self.vaga_a.pk).exists())

    def test_missing_object_is_404(self):
        self.client.force_login(self.user_b)
        response = self.client.get(reverse('vagas:minha_detalhe', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_get_delete_does_not_remove_vaga(self):
        self.client.force_login(self.empresa_a.user)
        response = self.client.get(reverse('vagas:excluir', args=[self.vaga_a.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Vaga.objects.filter(pk=self.vaga_a.pk).exists())

    def test_egressa_and_admin_cannot_use_company_routes(self):
        self.client.raise_request_exception = False
        for user in (self.egressa, self.admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('vagas:minhas')).status_code, 403)
            self.assertEqual(self.client.get(reverse('vagas:criar')).status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse('vagas:minhas'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/?next=', response['Location'])

    def test_empresa_without_profile_is_forbidden(self):
        user = CustomUser.objects.create_user(
            email='sem-perfil@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        self.client.raise_request_exception = False
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('vagas:minhas')).status_code, 403)
