from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import ProdutoServico


def _delete_file(storage, name):
    if not name:
        return
    try:
        storage.delete(name)
    except FileNotFoundError:
        pass


@receiver(pre_save, sender=ProdutoServico)
def remove_imagem_substituida(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        anterior = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    nome_anterior = anterior.imagem.name if anterior.imagem else None
    nome_atual = instance.imagem.name if instance.imagem else None
    if nome_anterior and nome_anterior != nome_atual:
        storage = anterior.imagem.storage
        transaction.on_commit(
            lambda: _delete_file(storage, nome_anterior)
        )


@receiver(post_delete, sender=ProdutoServico)
def remove_imagem_excluida(sender, instance, **kwargs):
    if not instance.imagem:
        return
    storage = instance.imagem.storage
    nome = instance.imagem.name
    transaction.on_commit(lambda: _delete_file(storage, nome))
