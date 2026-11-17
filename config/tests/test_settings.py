from django.conf import settings
from django.test import TestCase


class ProductionInfrastructureSettingsTests(TestCase):
    def test_test_suite_uses_local_cache_and_safe_storage(self):
        self.assertFalse(settings.PRODUCAO)
        self.assertIn('locmem', settings.CACHES['default']['BACKEND'].lower())
        self.assertIn(
            'FileSystemStorage',
            settings.STORAGES['default']['BACKEND'],
        )

    def test_health_endpoint_is_public(self):
        response = self.client.get('/saude/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')
