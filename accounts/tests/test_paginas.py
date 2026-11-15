from django.core.cache import cache
from django.test import TestCase


class PaginasTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_terms_and_privacy_are_public_drafts(self):
        for path in ('/termos/', '/privacidade/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Documento em elaboração.')

    def test_registration_and_login_pages_have_document_links(self):
        for path in ('/cadastro/egressa/', '/cadastro/empresa/', '/login/'):
            response = self.client.get(path)
            self.assertContains(response, 'href="/termos/"')
            self.assertContains(response, 'href="/privacidade/"')
