from django.contrib import admin
from django.contrib import messages

from .models import Candidatura, EmpresaProfile, Vaga


@admin.register(EmpresaProfile)
class EmpresaProfileAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'cnpj', 'user', 'is_aprovada', 'usuario_ativo')
    list_filter = ('is_aprovada', 'user__is_active')
    ordering = ('is_aprovada', 'razao_social')
    search_fields = ('razao_social', 'cnpj', 'user__email')
    raw_id_fields = ('user',)
    list_select_related = ('user',)
    actions = ('aprovar_empresas', 'revogar_aprovacao')

    @admin.display(boolean=True, description='conta ativa')
    def usuario_ativo(self, obj):
        return obj.user.is_active

    @admin.action(description='Aprovar empresas', permissions=['change'])
    def aprovar_empresas(self, request, queryset):
        pendentes = queryset.filter(user__is_active=False).count()
        total = queryset.update(is_aprovada=True)
        self.message_user(request, f'{total} empresa(s) aprovada(s).')
        if pendentes:
            self.message_user(
                request,
                f'Atenção: {pendentes} empresa(s) aprovada(s) ainda não '
                'confirmaram o e-mail e só poderão entrar depois da confirmação.',
                level=messages.WARNING,
            )

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
    list_display = ('candidata', 'vaga', 'data_candidatura', 'aceitou_compartilhar_em')
    list_filter = ('data_candidatura',)
    search_fields = ('candidata__email', 'vaga__titulo')
    list_select_related = ('candidata', 'vaga')
    readonly_fields = (
        'vaga', 'candidata', 'data_candidatura', 'aceitou_compartilhar_em',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
