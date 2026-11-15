import os

from django.core.exceptions import ValidationError
from django.test import override_settings

from .helpers import VitrineTestCase
from vitrine.forms import ProdutoServicoForm
from vitrine.imagens import processar_imagem


class ImagemVitrineTests(VitrineTestCase):
    def valid_data(self, upload):
        return {
            'nome_exibicao': 'Ateliê',
            'titulo': 'Item',
            'descricao': 'Descrição',
            'categoria': 'PRODUTO',
            'contato': 'contato',
            'imagem': upload,
            'aceito_publicar': True,
        }

    def test_jpeg_aceito(self):
        form = ProdutoServicoForm(data=self.valid_data(self.image_upload()), files={'imagem': self.image_upload()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_png_aceito(self):
        upload = self.image_upload('imagem.png', 'PNG')
        form = ProdutoServicoForm(data=self.valid_data(upload), files={'imagem': upload})
        self.assertTrue(form.is_valid(), form.errors)

    def test_webp_aceito(self):
        upload = self.image_upload('imagem.webp', 'WEBP')
        form = ProdutoServicoForm(data=self.valid_data(upload), files={'imagem': upload})
        self.assertTrue(form.is_valid(), form.errors)

    def test_nome_original_nao_e_preservado(self):
        upload = self.image_upload('minha-foto-casa.jpg')
        result = processar_imagem(upload)
        self.assertNotIn('minha-foto-casa.jpg', result.name)
        self.assertRegex(os.path.basename(result.name), r'^[0-9a-f]{32}\.jpg$')

    def test_exif_nao_e_gravado(self):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        output = BytesIO()
        from PIL import Image
        from PIL.TiffImagePlugin import IFDRational
        image = Image.new('RGB', (100, 100), 'white')
        exif = Image.Exif()
        exif[34853] = {
            1: 'N',
            2: (
                IFDRational(40, 1),
                IFDRational(0, 1),
                IFDRational(0, 1),
            ),
            3: 'W',
            4: (
                IFDRational(74, 1),
                IFDRational(0, 1),
                IFDRational(0, 1),
            ),
        }
        image.save(output, format='JPEG', exif=exif)
        upload = SimpleUploadedFile(
            'com-exif.jpg',
            output.getvalue(),
            content_type='image/jpeg',
        )
        result = processar_imagem(upload)
        result.seek(0)
        with Image.open(result) as image:
            self.assertEqual(len(image.getexif()), 0)

    def test_texto_renomeado_rejeitado(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile(
            'texto.jpg',
            b'not an image',
            content_type='image/jpeg',
        )
        with self.assertRaises(ValidationError):
            processar_imagem(upload)

    def test_svg_rejeitado(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile('imagem.svg', b'<svg></svg>', content_type='image/svg+xml')
        with self.assertRaises(ValidationError):
            processar_imagem(upload)

    def test_gif_rejeitado(self):
        upload = self.image_upload('imagem.gif', 'GIF')
        with self.assertRaisesMessage(ValidationError, 'Use uma imagem JPEG, PNG ou WEBP.'):
            processar_imagem(upload)

    @override_settings(VITRINE_IMAGEM_MAX_BYTES=10)
    def test_arquivo_acima_do_limite_rejeitado(self):
        with self.assertRaisesMessage(ValidationError, 'A imagem deve ter no máximo 2 MB.'):
            processar_imagem(self.image_upload())

    @override_settings(VITRINE_IMAGEM_MAX_PIXELS=100)
    def test_imagem_acima_do_limite_de_pixels_rejeitada(self):
        with self.assertRaisesMessage(ValidationError, 'A imagem é grande demais.'):
            processar_imagem(self.image_upload(size=(11, 11)))

    def test_imagem_grande_e_reduzida(self):
        result = processar_imagem(self.image_upload(size=(2000, 1000)))
        result.seek(0)
        from PIL import Image
        with Image.open(result) as image:
            self.assertLessEqual(max(image.size), 1600)

    def test_criar_sem_imagem_funciona(self):
        owner = self.create_user('imagem-owner@example.com')
        form = ProdutoServicoForm(data={
            'nome_exibicao': 'Ateliê',
            'titulo': 'Sem foto',
            'descricao': 'Descrição',
            'categoria': 'PRODUTO',
            'contato': 'contato',
            'aceito_publicar': True,
        })
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save(commit=False)
        item.owner = owner
        item.save()
        self.assertFalse(item.imagem)

    def test_trocar_imagem_apaga_arquivo_antigo(self):
        owner = self.create_user('troca@example.com')
        first = processar_imagem(self.image_upload())
        item = self.create_item(owner, imagem=first)
        old_path = item.imagem.path
        self.assertTrue(os.path.exists(old_path))
        replacement = processar_imagem(self.image_upload('nova.jpg'))
        item.imagem = replacement
        with self.captureOnCommitCallbacks(execute=True):
            item.save()
        self.assertFalse(os.path.exists(old_path))

    def test_excluir_item_apaga_arquivo(self):
        owner = self.create_user('excluir-imagem@example.com')
        item = self.create_item(owner, imagem=processar_imagem(self.image_upload()))
        path = item.imagem.path
        self.assertTrue(os.path.exists(path))
        with self.captureOnCommitCallbacks(execute=True):
            item.delete()
        self.assertFalse(os.path.exists(path))
