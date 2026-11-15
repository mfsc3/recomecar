# accounts/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('O e-mail deve ser informado.')
        normalized_email = self.normalize_email(email).lower()
        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields['role'] = CustomUser.Role.ADMIN
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        EGRESSA = 'EGRESSA', 'Egressa'
        EMPRESA = 'EMPRESA', 'Empresa'

    username = None
    email = models.EmailField(unique=True, verbose_name='e-mail')
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.EGRESSA,
        db_index=True,
    )
    aceitou_termo = models.BooleanField(default=False)
    aceitou_termo_em = models.DateTimeField(null=True, blank=True)
    versao_termo = models.CharField(max_length=40, blank=True, default='')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return self.email

    @property
    def is_egressa(self):
        return self.role == self.Role.EGRESSA

    @property
    def is_empresa(self):
        return self.role == self.Role.EMPRESA

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
