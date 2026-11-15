import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


def caminho_imagem(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in {'.jpg', '.png', '.webp'}:
        raise ValueError('Extensão de imagem não permitida.')
    return f'vitrine/{uuid.uuid4().hex}{ext}'


class ProdutoServico(models.Model):
    class Categoria(models.TextChoices):
        PRODUTO = 'PRODUTO', 'Produto'
        SERVICO = 'SERVICO', 'Serviço'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='produtos_servicos',
        limit_choices_to={'role': 'EGRESSA'},
    )
    nome_exibicao = models.CharField(
        max_length=80,
        help_text=(
            'Nome que aparecerá publicamente. Pode ser o nome do seu negócio '
            'ou um apelido.'
        ),
    )
    titulo = models.CharField(max_length=120)
    descricao = models.TextField(
        max_length=2000,
        help_text=(
            'Descreva o produto ou serviço. Não inclua dados pessoais que '
            'você não queira tornar públicos.'
        ),
    )
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    categoria = models.CharField(max_length=10, choices=Categoria.choices)
    imagem = models.ImageField(upload_to=caminho_imagem, null=True, blank=True)
    contato = models.CharField(
        max_length=150,
        help_text=(
            'Único dado de contato exibido ao público (WhatsApp, Instagram '
            'ou e-mail). Informe só o que você aceita divulgar.'
        ),
    )
    is_ativo = models.BooleanField(default=True, db_index=True)
    publicacao_aceita_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'produto ou serviço'
        verbose_name_plural = 'produtos e serviços'

    def __str__(self):
        return f'{self.titulo} ({self.nome_exibicao})'

    def clean(self):
        super().clean()
        if self.owner_id and self.owner.role != 'EGRESSA':
            raise ValidationError(
                'Somente contas de egressas podem ter itens na vitrine.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
