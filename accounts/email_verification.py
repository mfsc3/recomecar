import logging

from allauth.account.internal.flows.email_verification import (
    send_verification_email_to_address,
)
from allauth.account.models import EmailAddress


logger = logging.getLogger(__name__)


def enviar_confirmacao(request, user):
    email = user.email.strip().lower()
    try:
        address, _ = EmailAddress.objects.get_or_create(
            user=user,
            email=email,
            defaults={'primary': True, 'verified': False},
        )
        changed = []
        if address.primary is not True:
            address.primary = True
            changed.append('primary')
        if address.verified is not False:
            address.verified = False
            changed.append('verified')
        if changed:
            address.save(update_fields=changed)
        return send_verification_email_to_address(request, address, signup=True)
    except Exception:
        logger.exception('Falha ao enviar confirmação para user_id=%s', user.pk)
        return False
