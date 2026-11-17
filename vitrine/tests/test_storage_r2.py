from unittest.mock import patch

from django.test import SimpleTestCase

from storages.backends.s3 import S3Storage


class R2StorageTests(SimpleTestCase):
    def test_private_storage_generates_signed_url(self):
        storage = S3Storage(
            bucket_name='recomecar-test',
            endpoint_url='https://r2.example',
            access_key='access',
            secret_key='secret',
            region_name='auto',
            signature_version='s3v4',
            querystring_auth=True,
            querystring_expire=3600,
        )
        with patch.object(
            storage.connection.meta.client,
            'generate_presigned_url',
            return_value='https://r2.example/item?X-Amz-Signature=test',
        ) as generate:
            url = storage.url('vitrine/item.jpg')

        self.assertIn('X-Amz-Signature=', url)
        generate.assert_called_once()
        self.assertEqual(
            generate.call_args.kwargs['ExpiresIn'],
            3600,
        )
