import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import format_html
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    TemplateView,
    UpdateView,
)

from allauth.account.internal.flows.email_verification import (
    send_verification_email_to_address,
)
from axes.helpers import get_client_ip_address

from vagas.models import EmpresaProfile
from allauth.account.models import EmailAddress

from .forms import (
    CadastroEmpresaForm,
    CadastroEgressaForm,
    EmailLoginForm,
    EmailReenvioForm,
    CurriculoForm,
    EscolaridadeForm,
    ExperienciaForm,
)
from .mixins import EgressaRequiredMixin
from .email_verification import enviar_confirmacao
from .models import Curriculo, CustomUser, Escolaridade, Experiencia
from .ratelimit import permitido


logger = logging.getLogger(__name__)


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
        user.is_active = False
        user.aceitou_termo_em = timezone.now()
        user.versao_termo = settings.TERMOS_VERSAO
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
                EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    primary=True,
                    verified=False,
                )
        except (IntegrityError, ValidationError):
            form.add_error(
                None,
                'Não foi possível concluir o cadastro. Revise os dados e tente novamente.',
            )
            return self.form_invalid(form)
        if enviar_confirmacao(self.request, user):
            messages.success(
                self.request,
                'Cadastro realizado. Enviamos um e-mail de confirmação; '
                'clique no link para ativar sua conta.',
            )
        else:
            messages.warning(
                self.request,
                format_html(
                    'Cadastro realizado, mas não foi possível enviar o e-mail. '
                    '<a href="{}">Solicite um novo envio</a>.',
                    reverse('accounts:reenviar_confirmacao'),
                ),
            )
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
                EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    primary=True,
                    verified=False,
                )
        except (IntegrityError, ValidationError):
            form.add_error(
                None,
                'Não foi possível concluir o cadastro. Revise os dados e tente novamente.',
            )
            return self.form_invalid(form)
        if enviar_confirmacao(self.request, user):
            messages.success(
                self.request,
                'Cadastro realizado. Enviamos um e-mail de confirmação; '
                'clique no link para ativar sua conta.',
            )
        else:
            messages.warning(
                self.request,
                format_html(
                    'Cadastro realizado, mas não foi possível enviar o e-mail. '
                    '<a href="{}">Solicite um novo envio</a>.',
                    reverse('accounts:reenviar_confirmacao'),
                ),
            )
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


class RateLimitedPasswordResetView(PasswordResetView):
    def post(self, request, *args, **kwargs):
        ip = get_client_ip_address(request) or 'unknown'
        if not permitido('password_reset_ip', ip, *settings.RATE_LIMIT_IP):
            return render(request, 'accounts/rate_limited.html', status=429)

        email = request.POST.get('email', '').strip().lower()
        if not permitido(
            'password_reset_email', email, *settings.RATE_LIMIT_EMAIL
        ):
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)


class ReenviarConfirmacaoView(FormView):
    template_name = 'accounts/reenviar_confirmacao.html'
    form_class = EmailReenvioForm

    def form_valid(self, form):
        ip = get_client_ip_address(self.request) or 'unknown'
        if not permitido('resend_confirmation_ip', ip, *settings.RATE_LIMIT_IP):
            return render(
                self.request,
                'accounts/rate_limited.html',
                status=429,
            )

        email = form.cleaned_data['email']
        email_allowed = permitido(
            'resend_confirmation_email', email, *settings.RATE_LIMIT_EMAIL
        )
        if email_allowed:
            user = CustomUser.objects.filter(
                email__iexact=email,
                role__in=(CustomUser.Role.EGRESSA, CustomUser.Role.EMPRESA),
                is_active=False,
                last_login__isnull=True,
            ).first()
            if user:
                address = EmailAddress.objects.filter(
                    user=user,
                    email__iexact=email,
                    verified=False,
                ).first()
                if address:
                    try:
                        send_verification_email_to_address(
                            self.request,
                            address,
                        )
                    except Exception:
                        logger.exception(
                            'Falha ao reenviar confirmação para user_id=%s',
                            user.pk,
                        )

        messages.success(
            self.request,
            'Se houver uma conta aguardando confirmação, enviaremos um novo e-mail.',
        )
        return self.render_to_response(self.get_context_data(form=form))


class TermosView(TemplateView):
    template_name = 'accounts/termos.html'


class PrivacidadeView(TemplateView):
    template_name = 'accounts/privacidade.html'


class CurriculoDetailView(EgressaRequiredMixin, TemplateView):
    template_name = 'accounts/curriculo_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curriculo, _ = Curriculo.objects.get_or_create(user=self.request.user)
        context['curriculo'] = curriculo
        context['experiencias'] = curriculo.experiencias.all()
        context['escolaridades'] = curriculo.escolaridades.all()
        return context


class CurriculoUpdateView(EgressaRequiredMixin, UpdateView):
    model = Curriculo
    form_class = CurriculoForm
    template_name = 'accounts/curriculo_form.html'
    success_url = reverse_lazy('accounts:curriculo')

    def get_object(self, queryset=None):
        curriculo, _ = Curriculo.objects.get_or_create(user=self.request.user)
        return curriculo

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Currículo atualizado.')
        return response


class ExperienciaCreateView(EgressaRequiredMixin, CreateView):
    model = Experiencia
    form_class = ExperienciaForm
    template_name = 'accounts/experiencia_form.html'
    success_url = reverse_lazy('accounts:curriculo')

    def dispatch(self, request, *args, **kwargs):
        self.curriculo_atual, _ = Curriculo.objects.get_or_create(
            user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.curriculo = self.curriculo_atual
        response = super().form_valid(form)
        messages.success(self.request, 'Experiência adicionada.')
        return response


class ExperienciaUpdateView(EgressaRequiredMixin, UpdateView):
    model = Experiencia
    form_class = ExperienciaForm
    template_name = 'accounts/experiencia_form.html'
    success_url = reverse_lazy('accounts:curriculo')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Experiencia,
            pk=self.kwargs['pk'],
            curriculo__user=self.request.user,
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Experiência atualizada.')
        return response


class ExperienciaDeleteView(EgressaRequiredMixin, DeleteView):
    model = Experiencia
    template_name = 'accounts/experiencia_confirm_delete.html'
    success_url = reverse_lazy('accounts:curriculo')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Experiencia,
            pk=self.kwargs['pk'],
            curriculo__user=self.request.user,
        )


class EscolaridadeCreateView(EgressaRequiredMixin, CreateView):
    model = Escolaridade
    form_class = EscolaridadeForm
    template_name = 'accounts/escolaridade_form.html'
    success_url = reverse_lazy('accounts:curriculo')

    def dispatch(self, request, *args, **kwargs):
        self.curriculo_atual, _ = Curriculo.objects.get_or_create(
            user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.curriculo = self.curriculo_atual
        response = super().form_valid(form)
        messages.success(self.request, 'Escolaridade adicionada.')
        return response


class EscolaridadeUpdateView(EgressaRequiredMixin, UpdateView):
    model = Escolaridade
    form_class = EscolaridadeForm
    template_name = 'accounts/escolaridade_form.html'
    success_url = reverse_lazy('accounts:curriculo')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Escolaridade,
            pk=self.kwargs['pk'],
            curriculo__user=self.request.user,
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Escolaridade atualizada.')
        return response


class EscolaridadeDeleteView(EgressaRequiredMixin, DeleteView):
    model = Escolaridade
    template_name = 'accounts/escolaridade_confirm_delete.html'
    success_url = reverse_lazy('accounts:curriculo')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Escolaridade,
            pk=self.kwargs['pk'],
            curriculo__user=self.request.user,
        )
