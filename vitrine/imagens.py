from io import BytesIO
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


EXT = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}


def processar_imagem(arquivo):
    if arquivo.size > settings.VITRINE_IMAGEM_MAX_BYTES:
        raise ValidationError('A imagem deve ter no máximo 2 MB.')
    try:
        img = Image.open(arquivo)
        img.verify()
        arquivo.seek(0)
        img = Image.open(arquivo)
        formato = img.format
        if formato == 'MPO':
            formato = 'JPEG'
        if formato not in EXT:
            raise ValidationError('Use uma imagem JPEG, PNG ou WEBP.')
        if img.width * img.height > settings.VITRINE_IMAGEM_MAX_PIXELS:
            raise ValidationError('A imagem é grande demais.')
        img = ImageOps.exif_transpose(img)
        img.thumbnail((settings.VITRINE_IMAGEM_LADO_MAX,) * 2)
        if formato == 'JPEG' and img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        buf = BytesIO()
        opts = {'quality': 85} if formato in ('JPEG', 'WEBP') else {}
        img.save(buf, format=formato, **opts)
    except ValidationError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
        ValueError,
    ):
        raise ValidationError('Arquivo de imagem inválido.')
    return ContentFile(buf.getvalue(), name=f'{uuid4().hex}.{EXT[formato]}')
