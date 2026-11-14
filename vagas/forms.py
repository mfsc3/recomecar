from django import forms

from .models import Vaga


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
