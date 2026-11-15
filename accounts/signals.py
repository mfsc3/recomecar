from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from allauth.account.signals import email_confirmed
from allauth.socialaccount.models import SocialAccount

from .models import CustomUser


@receiver(email_confirmed)
def ativar_conta_apos_confirmacao(request, email_address, **kwargs):
    user = email_address.user
    if (
        not user.is_active
        and user.email.lower() == email_address.email.lower()
        and user.role in {CustomUser.Role.EGRESSA, CustomUser.Role.EMPRESA}
        and not user.is_staff
        and not user.is_superuser
        and user.last_login is None
    ):
        user.is_active = True
        user.save(update_fields=['is_active'])


@receiver(user_logged_in)
def limpar_extra_data_social(request, user, **kwargs):
    SocialAccount.objects.filter(user=user).exclude(extra_data={}).update(
        extra_data={}
    )
