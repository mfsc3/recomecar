from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView

from vagas.models import EmpresaProfile

from .forms import CadastroEmpresaForm, CadastroEgressaForm, EmailLoginForm
from .models import CustomUser


class PublicCadastroMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:painel')
        return super().dispatch(request, *args, **kwargs)

    def _prepare_user(self, form):
        user = form.save(commit=False)
        user.role = self.role_destino
        user.is_staff = False
        user.is_superuser = False
        user.aceitou_termo = True
        return user


class CadastroEgressaView(PublicCadastroMixin, FormView):
    template_name = 'accounts/cadastro_egressa.html'
    form_class = CadastroEgressaForm
    role_destino = CustomUser.Role.EGRESSA

    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = self._prepare_user(form)
                user.save()
        except (IntegrityError, ValidationError):
            form.add_error(
                None,
                'Não foi possível concluir o cadastro. Revise os dados e tente novamente.',
            )
            return self.form_invalid(form)
        messages.success(self.request, 'Cadastro realizado com sucesso. Faça seu login.')
        return redirect('accounts:login')


class CadastroEmpresaView(PublicCadastroMixin, FormView):
    template_name = 'accounts/cadastro_empresa.html'
    form_class = CadastroEmpresaForm
    role_destino = CustomUser.Role.EMPRESA

    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = self._prepare_user(form)
                user.save()
                EmpresaProfile.objects.create(
                    user=user,
                    cnpj=form.cleaned_data['cnpj'],
                    razao_social=form.cleaned_data['razao_social'],
                )
        except (IntegrityError, ValidationError):
            form.add_error(
                None,
                'Não foi possível concluir o cadastro. Revise os dados e tente novamente.',
            )
            return self.form_invalid(form)
        messages.success(self.request, 'Cadastro realizado com sucesso. Faça seu login.')
        return redirect('accounts:login')


class EmailLoginView(LoginView):
    authentication_form = EmailLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class PostOnlyLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['POST'])


class PainelView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/painel.html'
