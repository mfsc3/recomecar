from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import EgressaRequiredMixin

from .forms import ProdutoServicoForm
from .models import ProdutoServico


class VitrineListaView(ListView):
    model = ProdutoServico
    template_name = 'vitrine/lista.html'
    context_object_name = 'itens'
    paginate_by = 12

    def get_queryset(self):
        return ProdutoServico.objects.filter(
            is_ativo=True,
            owner__is_active=True,
            owner__role='EGRESSA',
        ).only(
            'id',
            'nome_exibicao',
            'titulo',
            'preco',
            'categoria',
            'imagem',
            'criado_em',
        )


class VitrineDetalheView(DetailView):
    model = ProdutoServico
    template_name = 'vitrine/detalhe.html'
    context_object_name = 'item'

    def get_queryset(self):
        return ProdutoServico.objects.filter(
            is_ativo=True,
            owner__is_active=True,
            owner__role='EGRESSA',
        ).only(
            'id',
            'nome_exibicao',
            'titulo',
            'preco',
            'categoria',
            'imagem',
            'criado_em',
            'descricao',
            'contato',
        )


class MinhaVitrineView(EgressaRequiredMixin, ListView):
    model = ProdutoServico
    template_name = 'vitrine/minha.html'
    context_object_name = 'itens'

    def get_queryset(self):
        return ProdutoServico.objects.filter(owner=self.request.user)


class ProdutoCreateView(EgressaRequiredMixin, CreateView):
    model = ProdutoServico
    form_class = ProdutoServicoForm
    template_name = 'vitrine/produto_form.html'
    success_url = reverse_lazy('vitrine:minha')

    def form_valid(self, form):
        if ProdutoServico.objects.filter(
            owner=self.request.user
        ).count() >= settings.VITRINE_MAX_ITENS:
            form.add_error(None, 'Você atingiu o limite de itens na vitrine.')
            return self.form_invalid(form)
        form.instance.owner = self.request.user
        form.instance.publicacao_aceita_em = timezone.now()
        response = super().form_valid(form)
        messages.success(self.request, 'Item publicado com sucesso.')
        return response


class ProdutoUpdateView(EgressaRequiredMixin, UpdateView):
    model = ProdutoServico
    form_class = ProdutoServicoForm
    template_name = 'vitrine/produto_form.html'
    success_url = reverse_lazy('vitrine:minha')

    def get_object(self, queryset=None):
        return get_object_or_404(
            ProdutoServico,
            pk=self.kwargs['pk'],
            owner=self.request.user,
        )

    def form_valid(self, form):
        form.instance.publicacao_aceita_em = timezone.now()
        response = super().form_valid(form)
        messages.success(self.request, 'Item atualizado com sucesso.')
        return response


class ProdutoDeleteView(EgressaRequiredMixin, DeleteView):
    model = ProdutoServico
    template_name = 'vitrine/produto_confirm_delete.html'
    success_url = reverse_lazy('vitrine:minha')

    def get_object(self, queryset=None):
        return get_object_or_404(
            ProdutoServico,
            pk=self.kwargs['pk'],
            owner=self.request.user,
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Item excluído com sucesso.')
        return response
