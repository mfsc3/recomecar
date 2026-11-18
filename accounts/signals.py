import logging

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from allauth.account.signals import email_confirmed
from allauth.socialaccount.models import SocialAccount

from .models import CustomUser


logger = logging.getLogger(__name__)


@receiver(email_confirmed)
def ativar_conta_apos_confirmacao(request, email_address, **kwargs):
    user = email_address.user
    if user.email.lower() != email_address.email.lower():
        return
    if user.is_active:
        return
    if not email_address.verified:
        return
    if user.role not in {CustomUser.Role.EGRESSA, CustomUser.Role.EMPRESA}:
        return
    if user.is_staff or user.is_superuser:
        return
    if user.last_login is not None:
        return
    user.is_active = True
    user.save(update_fields=['is_active'])
    logger.info('Conta ativada após confirmação pk=%s', user.pk)


@receiver(user_logged_in)
def limpar_extra_data_social(request, user, **kwargs):
    SocialAccount.objects.filter(user=user).exclude(extra_data={}).update(
        extra_data={}
    )
