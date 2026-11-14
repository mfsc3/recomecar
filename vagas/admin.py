from django.contrib import admin

from .models import Candidatura, EmpresaProfile, Vaga


@admin.register(EmpresaProfile)
class EmpresaProfileAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'cnpj', 'user', 'is_aprovada')
    list_filter = ('is_aprovada',)
    ordering = ('is_aprovada', 'razao_social')
    search_fields = ('razao_social', 'cnpj', 'user__email')
    raw_id_fields = ('user',)
    actions = ('aprovar_empresas', 'revogar_aprovacao')

    @admin.action(description='Aprovar empresas', permissions=['change'])
    def aprovar_empresas(self, request, queryset):
        total = queryset.update(is_aprovada=True)
        self.message_user(request, f'{total} empresa(s) aprovada(s).')

    @admin.action(description='Revogar aprovação', permissions=['change'])
    def revogar_aprovacao(self, request, queryset):
        total = queryset.update(is_aprovada=False)
        self.message_user(request, f'Aprovação revogada de {total} empresa(s).')


@admin.register(Vaga)
class VagaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'salario', 'ativa', 'criado_em')
    list_filter = ('ativa', 'criado_em', 'empresa__is_aprovada')
    search_fields = ('titulo', 'empresa__razao_social')
    readonly_fields = ('criado_em',)
    list_select_related = ('empresa',)
    actions = ('desativar_vagas',)

    @admin.action(description='Desativar vagas selecionadas')
    def desativar_vagas(self, request, queryset):
        queryset.update(ativa=False)


@admin.register(Candidatura)
class CandidaturaAdmin(admin.ModelAdmin):
    list_display = ('candidata', 'vaga', 'data_candidatura')
    list_filter = ('data_candidatura',)
    search_fields = ('candidata__email', 'vaga__titulo')
    list_select_related = ('candidata', 'vaga')
    readonly_fields = ('vaga', 'candidata', 'data_candidatura')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
