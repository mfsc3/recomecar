# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import Curriculo, CustomUser, Escolaridade, Experiencia


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    ordering = ('email',)
    list_display = (
        'email', 'first_name', 'last_name', 'role', 'aceitou_termo',
        'aceitou_termo_em', 'versao_termo', 'is_active', 'is_staff',
    )
    list_filter = ('role', 'aceitou_termo', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações pessoais', {'fields': ('first_name', 'last_name')}),
        ('Perfil e consentimento', {'fields': (
            'role', 'aceitou_termo', 'aceitou_termo_em', 'versao_termo',
        )}),
        ('Permissões', {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
        )}),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'aceitou_termo', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('aceitou_termo_em', 'versao_termo')


@admin.register(Curriculo)
class CurriculoAdmin(admin.ModelAdmin):
    list_display = ('user', 'atualizado_em')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    readonly_fields = ('criado_em', 'atualizado_em')


@admin.register(Experiencia)
class ExperienciaAdmin(admin.ModelAdmin):
    list_display = ('cargo', 'empresa_nome', 'curriculo', 'data_inicio', 'data_fim')
    search_fields = ('empresa_nome', 'cargo', 'curriculo__user__email')
    raw_id_fields = ('curriculo',)


@admin.register(Escolaridade)
class EscolaridadeAdmin(admin.ModelAdmin):
    list_display = ('curso', 'instituicao', 'nivel', 'status', 'curriculo')
    search_fields = ('instituicao', 'curso', 'curriculo__user__email')
    raw_id_fields = ('curriculo',)
