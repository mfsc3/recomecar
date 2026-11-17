from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase

from config.settings import _validate_storage_backend


class StorageGuardTests(SimpleTestCase):
    """Guard puro — não toca banco, roda rápido."""

    FS = 'django.core.files.storage.FileSystemStorage'
    S3 = 'storages.backends.s3.S3Storage'

    def test_levanta_quando_debug_false_fs_e_nao_teste(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            _validate_storage_backend(
                debug=False, storage_backend=self.FS, is_test=False,
            )
        self.assertIn('R2 não configurado', str(ctx.exception))
        self.assertIn('Mini-Sprint 8.1', str(ctx.exception))

    def test_nao_levanta_quando_debug_true(self):
        _validate_storage_backend(
            debug=True, storage_backend=self.FS, is_test=False,
        )

    def test_nao_levanta_quando_modo_teste(self):
        _validate_storage_backend(
            debug=False, storage_backend=self.FS, is_test=True,
        )

    def test_nao_levanta_quando_r2_configurado(self):
        _validate_storage_backend(
            debug=False, storage_backend=self.S3, is_test=False,
        )

    def test_settings_atuais_passam_pelo_guard(self):
        from django.conf import settings
        _validate_storage_backend(
            debug=settings.DEBUG,
            storage_backend=settings.STORAGES['default']['BACKEND'],
            is_test=True,
        )


class EndpointsAindaFuncionamTests(TestCase):
    """Testes que tocam banco (view pública consulta Vaga). TestCase, não SimpleTestCase."""

    def test_lista_publica_responde_200_apos_guard(self):
        from django.urls import reverse
        response = self.client.get(reverse('vagas:lista'))
        self.assertEqual(response.status_code, 200)
