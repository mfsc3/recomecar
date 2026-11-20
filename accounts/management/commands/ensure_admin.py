import os

from django.core.management.base import BaseCommand

from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Garante que o superusuario de producao existe, ativo e com senha conhecida.'

    def handle(self, *args, **options):
        self.stdout.write('=== Superusuarios atuais ===')
        qs = CustomUser.objects.filter(is_superuser=True)
        for u in qs:
            self.stdout.write(
                f'  {u.email} | active={u.is_active} staff={u.is_staff} '
                f'super={u.is_superuser} role={u.role} last_login={u.last_login}'
            )
        self.stdout.write(f'Total de superusuarios: {qs.count()}')

        email = (os.environ.get('ADMIN_EMAIL') or '').strip().lower()
        password = os.environ.get('ADMIN_PASSWORD') or ''
        reset_password = (os.environ.get('ADMIN_RESET_PASSWORD') or '').lower() == 'true'

        if not email:
            self.stdout.write('ADMIN_EMAIL vazio. Diagnostico encerrado, nada alterado.')
            return

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'role': CustomUser.Role.ADMIN,
            },
        )

        changed = created
        for field in ('is_staff', 'is_superuser', 'is_active'):
            if not getattr(user, field):
                setattr(user, field, True)
                changed = True
        if user.role != CustomUser.Role.ADMIN:
            user.role = CustomUser.Role.ADMIN
            changed = True

        if created or reset_password:
            if not password:
                self.stdout.write('ADMIN_PASSWORD vazio. Nao posso criar/redefinir senha.')
                return
            user.set_password(password)
            changed = True

        if changed:
            user.save()
            self.stdout.write(f'{"Criado" if created else "Atualizado"}: {user.email}')
        else:
            self.stdout.write(f'Sem mudanca (ja estava correto): {user.email}')

        self.stdout.write(
            f'  active={user.is_active} staff={user.is_staff} '
            f'super={user.is_superuser} role={user.role}'
        )

        if (os.environ.get('ADMIN_RESET_AXES') or '').lower() == 'true':
            from axes.utils import reset
            reset()
            self.stdout.write('Axes reset: todos os bloqueios de login foram limpos.')