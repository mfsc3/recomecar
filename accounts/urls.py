from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from .views import (
    CadastroEmpresaView,
    CadastroEgressaView,
    EmailLoginView,
    PrivacidadeView,
    PainelView,
    PostOnlyLogoutView,
    RateLimitedPasswordResetView,
    ReenviarConfirmacaoView,
    TermosView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', EmailLoginView.as_view(), name='login'),
    path('logout/', PostOnlyLogoutView.as_view(), name='logout'),
    path('cadastro/egressa/', CadastroEgressaView.as_view(), name='cadastro_egressa'),
    path('cadastro/empresa/', CadastroEmpresaView.as_view(), name='cadastro_empresa'),
    path('painel/', PainelView.as_view(), name='painel'),
    path('termos/', TermosView.as_view(), name='termos'),
    path('privacidade/', PrivacidadeView.as_view(), name='privacidade'),
    path(
        'email/reenviar/',
        ReenviarConfirmacaoView.as_view(),
        name='reenviar_confirmacao',
    ),
    path(
        'senha/recuperar/',
        RateLimitedPasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='accounts/password_reset_email.txt',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('accounts:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'senha/recuperar/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'senha/redefinir/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'senha/redefinir/concluido/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
