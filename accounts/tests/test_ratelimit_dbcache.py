from django.conf import settings
from django.test import TestCase


class ProductionCacheConfigurationTests(TestCase):
    def test_axes_uses_database_handler(self):
        self.assertEqual(
            settings.AXES_HANDLER,
            'axes.handlers.database.AxesDatabaseHandler',
        )

    def test_test_suite_uses_non_database_cache(self):
        self.assertIn(
            'locmem',
            settings.CACHES['default']['BACKEND'].lower(),
        )
