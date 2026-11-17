# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.urls import reverse
from django.utils.html import format_html

from .models import Curriculo, CustomUser, Escolaridade, Experiencia
from vagas.models import EmpresaProfile
from vagas.validators import validar_cnpj


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'role', 'aceitou_termo')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'


class CadastroEgressaForm(UserCreationForm):
    first_name = forms.CharField(label='Nome')
    aceitou_termo = forms.BooleanField(
        required=True,
        label='Li e aceito os Termos de Uso e a Política de Privacidade',
        error_messages={'required': 'Você precisa aceitar os termos para continuar.'},
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'email', 'aceitou_termo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['aceitou_termo'].label = format_html(
            'Li e aceito os <a href="{}">Termos de Uso</a> e a '
            '<a href="{}">Política de Privacidade</a>',
            reverse('accounts:termos'),
            reverse('accounts:privacidade'),
        )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email


class CadastroEmpresaForm(CadastroEgressaForm):
    first_name = forms.CharField(label='Nome do responsável')
    razao_social = forms.CharField(max_length=255, label='Razão social')
    cnpj = forms.CharField(max_length=18, label='CNPJ')

    def clean_cnpj(self):
        cnpj = validar_cnpj(self.cleaned_data['cnpj'])
        if EmpresaProfile.objects.filter(cnpj=cnpj).exists():
            raise forms.ValidationError('Este CNPJ já está cadastrado.')
        return cnpj


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label='E-mail')
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'E-mail ou senha incorretos.',
        'inactive': 'E-mail ou senha incorretos.',
    }

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class EmailReenvioForm(forms.Form):
    email = forms.EmailField(label='E-mail')

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class CurriculoForm(forms.ModelForm):
    class Meta:
        model = Curriculo
        fields = ('resumo', 'habilidades')
        widgets = {
            'resumo': forms.Textarea(attrs={'class': 'w-full rounded border p-3', 'rows': 5}),
            'habilidades': forms.Textarea(attrs={'class': 'w-full rounded border p-3', 'rows': 4}),
        }


class ExperienciaForm(forms.ModelForm):
    class Meta:
        model = Experiencia
        fields = ('empresa_nome', 'cargo', 'data_inicio', 'data_fim', 'descricao')
        widgets = {
            'empresa_nome': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'cargo': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded border p-2'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded border p-2'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full rounded border p-3', 'rows': 4}),
        }


class EscolaridadeForm(forms.ModelForm):
    class Meta:
        model = Escolaridade
        fields = ('instituicao', 'curso', 'nivel', 'status', 'ano_inicio', 'ano_conclusao')
        widgets = {
            'instituicao': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'curso': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'nivel': forms.Select(attrs={'class': 'w-full rounded border p-2'}),
            'status': forms.Select(attrs={'class': 'w-full rounded border p-2'}),
            'ano_inicio': forms.NumberInput(attrs={'class': 'w-full rounded border p-2'}),
            'ano_conclusao': forms.NumberInput(attrs={'class': 'w-full rounded border p-2'}),
        }
