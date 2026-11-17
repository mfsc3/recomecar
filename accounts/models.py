# accounts/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


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


class Curriculo(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='curriculo',
        limit_choices_to={'role': 'EGRESSA'},
    )
    resumo = models.TextField(
        blank=True,
        verbose_name='resumo profissional',
    )
    habilidades = models.TextField(
        blank=True,
        help_text='Liste suas principais competências, separadas por vírgula.',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'currículo'
        verbose_name_plural = 'currículos'

    def __str__(self):
        return f'Currículo de {self.user.email}'

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != CustomUser.Role.EGRESSA:
            raise ValidationError(
                'Currículo só pode ser criado por usuárias Egressas.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Experiencia(models.Model):
    curriculo = models.ForeignKey(
        Curriculo,
        on_delete=models.CASCADE,
        related_name='experiencias',
    )
    empresa_nome = models.CharField(max_length=255)
    cargo = models.CharField(max_length=150)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_inicio', '-criado_em']
        verbose_name = 'experiência'
        verbose_name_plural = 'experiências'

    def clean(self):
        super().clean()
        if self.data_fim and self.data_fim < self.data_inicio:
            raise ValidationError(
                'A data de fim não pode ser anterior ao início.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Escolaridade(models.Model):
    class Nivel(models.TextChoices):
        FUNDAMENTAL = 'FUNDAMENTAL', 'Fundamental'
        MEDIO = 'MEDIO', 'Médio'
        TECNICO = 'TECNICO', 'Técnico'
        SUPERIOR = 'SUPERIOR', 'Superior'
        POS = 'POS', 'Pós-graduação'
        MESTRADO = 'MESTRADO', 'Mestrado'
        DOUTORADO = 'DOUTORADO', 'Doutorado'

    class Status(models.TextChoices):
        CONCLUIDO = 'CONCLUIDO', 'Concluído'
        CURSANDO = 'CURSANDO', 'Cursando'
        INCOMPLETO = 'INCOMPLETO', 'Incompleto'

    curriculo = models.ForeignKey(
        Curriculo,
        on_delete=models.CASCADE,
        related_name='escolaridades',
    )
    instituicao = models.CharField(max_length=255)
    curso = models.CharField(max_length=150)
    nivel = models.CharField(max_length=20, choices=Nivel.choices)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.CURSANDO,
    )
    ano_inicio = models.PositiveSmallIntegerField(null=True, blank=True)
    ano_conclusao = models.PositiveSmallIntegerField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ano_conclusao', 'instituicao']
        verbose_name = 'escolaridade'
        verbose_name_plural = 'escolaridades'

    def clean(self):
        super().clean()
        if (
            self.ano_conclusao
            and self.ano_inicio
            and self.ano_conclusao < self.ano_inicio
        ):
            raise ValidationError(
                'O ano de conclusão não pode ser anterior ao início.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
