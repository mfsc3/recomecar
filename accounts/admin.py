# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser


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
