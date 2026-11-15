from django import forms
from django.core.files.uploadedfile import UploadedFile

from .imagens import processar_imagem
from .models import ProdutoServico


class ProdutoServicoForm(forms.ModelForm):
    aceito_publicar = forms.BooleanField(
        required=True,
        label=(
            'Entendo que este anúncio e o contato informado ficam visíveis '
            'para qualquer pessoa, na internet.'
        ),
        error_messages={'required': 'Você precisa confirmar para publicar.'},
    )

    class Meta:
        model = ProdutoServico
        fields = (
            'nome_exibicao',
            'titulo',
            'descricao',
            'preco',
            'categoria',
            'imagem',
            'contato',
            'is_ativo',
        )
        widgets = {
            'nome_exibicao': forms.TextInput(
                attrs={'class': 'w-full rounded border p-2'}
            ),
            'titulo': forms.TextInput(
                attrs={'class': 'w-full rounded border p-2'}
            ),
            'descricao': forms.Textarea(
                attrs={'class': 'w-full rounded border p-2', 'rows': 5}
            ),
            'preco': forms.NumberInput(
                attrs={'class': 'w-full rounded border p-2', 'step': '0.01'}
            ),
            'categoria': forms.Select(
                attrs={'class': 'w-full rounded border p-2'}
            ),
            'imagem': forms.ClearableFileInput(
                attrs={'class': 'w-full rounded border p-2'}
            ),
            'contato': forms.TextInput(
                attrs={'class': 'w-full rounded border p-2'}
            ),
            'is_ativo': forms.CheckboxInput(attrs={'class': 'rounded'}),
        }

    def clean_imagem(self):
        arquivo = self.cleaned_data.get('imagem')
        if isinstance(arquivo, UploadedFile):
            return processar_imagem(arquivo)
        return arquivo

    def clean_titulo(self):
        return self.cleaned_data['titulo'].strip()

    def clean_nome_exibicao(self):
        return self.cleaned_data['nome_exibicao'].strip()

    def clean_contato(self):
        return self.cleaned_data['contato'].strip()
