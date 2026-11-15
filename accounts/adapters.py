from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils import timezone

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse


CustomUser = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def _bloquear(self, request):
        messages.error(
            request,
            'Não foi possível entrar com o Google. Se você já tem conta, '
            'entre com e-mail e senha.',
        )
        raise ImmediateHttpResponse(redirect('accounts:login'))

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            user = sociallogin.user
            if not user.is_active or user.role != CustomUser.Role.EGRESSA:
                self._bloquear(request)
            return

        verified_emails = [
            email.email.strip().lower()
            for email in sociallogin.email_addresses
            if email.verified
        ]
        if not verified_emails:
            self._bloquear(request)
        if CustomUser.objects.filter(email__iexact=verified_emails[0]).exists():
            self._bloquear(request)

    def _force_egressa(self, user, email=None):
        user.role = CustomUser.Role.EGRESSA
        user.aceitou_termo = True
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True
        if user.aceitou_termo_em is None:
            user.aceitou_termo_em = timezone.now()
            user.versao_termo = settings.TERMOS_VERSAO
        user.set_unusable_password()
        if email:
            user.email = email.strip().lower()
        return user

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        email = next(
            (
                item.email
                for item in sociallogin.email_addresses
                if item.verified
            ),
            data.get('email', ''),
        )
        return self._force_egressa(user, email)

    def save_user(self, request, sociallogin, form=None):
        self._force_egressa(sociallogin.user, sociallogin.user.email)
        return super().save_user(request, sociallogin, form=form)
