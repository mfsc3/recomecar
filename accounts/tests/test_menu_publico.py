from django.test import TestCase


class PublicMenuTests(TestCase):
    def test_logged_out_menu_uses_neutral_labels(self):
        response = self.client.get('/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Para Profissionais')
        self.assertContains(response, 'Para Empresas')
