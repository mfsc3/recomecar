# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from .models import CustomUser
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        message = 'E-mail ou senha incorretos.'
        self.error_messages['invalid_login'] = message
        self.error_messages['inactive'] = message

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()
