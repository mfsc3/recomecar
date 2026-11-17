from django.contrib import admin

from .models import ProdutoServico


@admin.register(ProdutoServico)
class ProdutoServicoAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'nome_exibicao',
        'categoria',
        'is_ativo',
        'owner',
        'criado_em',
    )
    list_filter = ('categoria', 'is_ativo')
    search_fields = ('titulo', 'nome_exibicao', 'owner__email')
    readonly_fields = (
        'owner',
        'imagem',
        'publicacao_aceita_em',
        'criado_em',
        'atualizado_em',
    )
    actions = ('desativar_itens',)

    def has_add_permission(self, request):
        return False

    @admin.action(
        description='Desativar itens selecionados',
        permissions=['change'],
    )
    def desativar_itens(self, request, queryset):
        queryset.update(is_ativo=False)
