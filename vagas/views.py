from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import EgressaRequiredMixin
from accounts.models import CustomUser

from .forms import VagaForm
from .models import Candidatura, Vaga
from .permissions import EmpresaAprovadaRequiredMixin, EmpresaComPerfilMixin


class VagaListaPublicaView(ListView):
    model = Vaga
    template_name = 'vagas/lista.html'
    context_object_name = 'vagas'
    paginate_by = 10

    def get_queryset(self):
        return Vaga.objects.filter(
            ativa=True,
            empresa__is_aprovada=True,
        ).select_related('empresa')


class VagaDetalhePublicaView(DetailView):
    model = Vaga
    template_name = 'vagas/detalhe_publica.html'
    context_object_name = 'vaga'

    def get_queryset(self):
        return Vaga.objects.filter(
            ativa=True,
            empresa__is_aprovada=True,
        ).select_related('empresa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['ja_candidatou'] = (
            user.is_authenticated
            and user.role == CustomUser.Role.EGRESSA
            and Candidatura.objects.filter(vaga=self.object, candidata=user).exists()
        )
        return context


class CandidatarView(EgressaRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        vaga = get_object_or_404(
            Vaga,
            pk=pk,
            ativa=True,
            empresa__is_aprovada=True,
        )
        try:
            with transaction.atomic():
                Candidatura.objects.create(vaga=vaga, candidata=request.user)
        except (ValidationError, IntegrityError):
            messages.info(request, 'Você já se candidatou a esta vaga.')
        else:
            messages.success(request, 'Candidatura enviada.')
        return redirect('vagas:detalhe_publica', pk=vaga.pk)


class MinhasVagasView(EmpresaComPerfilMixin, ListView):
    model = Vaga
    template_name = 'vagas/minhas.html'
    context_object_name = 'vagas'

    def get_queryset(self):
        return Vaga.objects.filter(empresa=self.empresa).annotate(
            total_candidaturas=Count('candidaturas')
        )


class VagaCreateView(EmpresaAprovadaRequiredMixin, CreateView):
    model = Vaga
    form_class = VagaForm
    template_name = 'vagas/vaga_form.html'
    success_url = reverse_lazy('vagas:minhas')

    def form_valid(self, form):
        form.instance.empresa = self.empresa
        response = super().form_valid(form)
        messages.success(self.request, 'Vaga criada com sucesso.')
        return response


class MinhaVagaDetailView(EmpresaComPerfilMixin, DetailView):
    model = Vaga
    template_name = 'vagas/minha_detalhe.html'
    context_object_name = 'vaga'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Vaga,
            pk=self.kwargs['pk'],
            empresa=self.empresa,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['candidatas'] = (
            Candidatura.objects
            .filter(vaga=self.object)
            .values('candidata__email', 'data_candidatura')
            .order_by('-data_candidatura')
        )
        return context


class VagaUpdateView(EmpresaAprovadaRequiredMixin, UpdateView):
    model = Vaga
    form_class = VagaForm
    template_name = 'vagas/vaga_form.html'
    success_url = reverse_lazy('vagas:minhas')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Vaga,
            pk=self.kwargs['pk'],
            empresa=self.empresa,
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Vaga atualizada com sucesso.')
        return response


class VagaDeleteView(EmpresaComPerfilMixin, DeleteView):
    model = Vaga
    template_name = 'vagas/vaga_confirm_delete.html'
    success_url = reverse_lazy('vagas:minhas')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Vaga,
            pk=self.kwargs['pk'],
            empresa=self.empresa,
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Vaga excluída com sucesso.')
        return response
