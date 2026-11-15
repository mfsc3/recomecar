from io import BytesIO
from tempfile import mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from accounts.models import CustomUser
from vitrine.models import ProdutoServico


class VitrineTestCase(TestCase):
    def setUp(self):
        self.media_root = mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        super().tearDown()
        import shutil
        shutil.rmtree(self.media_root, ignore_errors=True)

    def create_user(self, email, role=CustomUser.Role.EGRESSA, active=True):
        return CustomUser.objects.create_user(
            email=email,
            password='SenhaForte123!',
            role=role,
            is_active=active,
        )

    def create_item(self, owner, **kwargs):
        values = {
            'nome_exibicao': 'Ateliê Sol',
            'titulo': 'Bolos artesanais',
            'descricao': 'Bolos feitos sob encomenda.',
            'categoria': ProdutoServico.Categoria.PRODUTO,
            'contato': 'WhatsApp: 11999999999',
            'publicacao_aceita_em': None,
        }
        values.update(kwargs)
        return ProdutoServico.objects.create(owner=owner, **values)

    def image_upload(self, name='minha-foto-casa.jpg', image_format='JPEG', size=(100, 100)):
        output = BytesIO()
        Image.new('RGB', size, 'white').save(output, format=image_format)
        return SimpleUploadedFile(
            name,
            output.getvalue(),
            content_type=f'image/{image_format.lower()}',
        )
