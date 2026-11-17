from django import forms

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import EmpresaProfile, Vaga


ORIENTACAO_VAGA = (
    'Descreva apenas as competências e atividades da função. '
    'Não exija, pergunte ou mencione informações sobre histórico judicial '
    'ou passado pessoal da candidata. Vagas que fizerem isso poderão ser removidas.'
)


class VagaForm(forms.ModelForm):
    class Meta:
        model = Vaga
        fields = ('titulo', 'descricao', 'requisitos', 'salario', 'ativa')
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full rounded border p-2', 'rows': 5}),
            'requisitos': forms.Textarea(attrs={'class': 'w-full rounded border p-2', 'rows': 5}),
            'salario': forms.NumberInput(attrs={'class': 'w-full rounded border p-2', 'step': '0.01'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'rounded'}),
        }
        help_texts = {
            'descricao': ORIENTACAO_VAGA,
            'requisitos': ORIENTACAO_VAGA,
        }

    def clean_titulo(self):
        return self.cleaned_data['titulo'].strip()


class EmpresaProfileForm(forms.ModelForm):
    telefone_validator = RegexValidator(
        r'^[\d\s()+-]{8,20}$',
        'Telefone inválido.',
    )

    class Meta:
        model = EmpresaProfile
        fields = (
            'nome_fantasia',
            'logo',
            'endereco',
            'cidade',
            'estado',
            'responsavel_nome',
            'telefone',
            'descricao',
        )
        widgets = {
            'nome_fantasia': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'endereco': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'cidade': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'estado': forms.Select(attrs={'class': 'w-full rounded border p-2'}),
            'responsavel_nome': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'telefone': forms.TextInput(attrs={'class': 'w-full rounded border p-2'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full rounded border p-3', 'rows': 5}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo and hasattr(logo, 'size') and logo.size > 2 * 1024 * 1024:
            raise ValidationError('A imagem deve ter no máximo 2 MB.')
        return logo

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '')
        if telefone:
            self.telefone_validator(telefone)
        return telefone
