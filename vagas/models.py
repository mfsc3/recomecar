from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from accounts.models import CustomUser


class Estado(models.TextChoices):
    AC = 'AC', 'Acre'
    AL = 'AL', 'Alagoas'
    AP = 'AP', 'Amapá'
    AM = 'AM', 'Amazonas'
    BA = 'BA', 'Bahia'
    CE = 'CE', 'Ceará'
    DF = 'DF', 'Distrito Federal'
    ES = 'ES', 'Espírito Santo'
    GO = 'GO', 'Goiás'
    MA = 'MA', 'Maranhão'
    MT = 'MT', 'Mato Grosso'
    MS = 'MS', 'Mato Grosso do Sul'
    MG = 'MG', 'Minas Gerais'
    PA = 'PA', 'Pará'
    PB = 'PB', 'Paraíba'
    PR = 'PR', 'Paraná'
    PE = 'PE', 'Pernambuco'
    PI = 'PI', 'Piauí'
    RJ = 'RJ', 'Rio de Janeiro'
    RN = 'RN', 'Rio Grande do Norte'
    RS = 'RS', 'Rio Grande do Sul'
    RO = 'RO', 'Rondônia'
    RR = 'RR', 'Roraima'
    SC = 'SC', 'Santa Catarina'
    SP = 'SP', 'São Paulo'
    SE = 'SE', 'Sergipe'
    TO = 'TO', 'Tocantins'


class EmpresaProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='empresa_profile',
        limit_choices_to={'role': 'EMPRESA'},
    )
    cnpj = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                r'^\d{14}$',
                'O CNPJ deve conter exatamente 14 dígitos numéricos.',
            )
        ],
    )
    razao_social = models.CharField(max_length=255)
    is_aprovada = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='empresa aprovada',
        help_text='Somente o administrador pode aprovar. Empresas não aprovadas não publicam vagas.',
    )
    nome_fantasia = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='nome fantasia',
    )
    logo = models.ImageField(
        upload_to='empresas/logos/',
        blank=True,
        null=True,
    )
    endereco = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=100, blank=True, db_index=True)
    estado = models.CharField(
        max_length=2,
        blank=True,
        choices=Estado.choices,
        db_index=True,
    )
    responsavel_nome = models.CharField(max_length=150, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    descricao = models.TextField(
        blank=True,
        verbose_name='descrição institucional',
    )

    class Meta:
        verbose_name = 'perfil de empresa'
        verbose_name_plural = 'perfis de empresa'

    def __str__(self):
        return self.razao_social

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != CustomUser.Role.EMPRESA:
            raise ValidationError(
                'Somente usuárias com perfil Empresa podem ter um perfil de empresa.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Vaga(models.Model):
    empresa = models.ForeignKey(
        EmpresaProfile,
        on_delete=models.CASCADE,
        related_name='vagas',
    )
    titulo = models.CharField(max_length=150)
    descricao = models.TextField()
    requisitos = models.TextField()
    salario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    ativa = models.BooleanField(default=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'vaga'
        verbose_name_plural = 'vagas'

    def __str__(self):
        return f'{self.titulo} - {self.empresa.razao_social}'


class Candidatura(models.Model):
    vaga = models.ForeignKey(
        Vaga,
        on_delete=models.CASCADE,
        related_name='candidaturas',
    )
    candidata = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidaturas',
        limit_choices_to={'role': 'EGRESSA'},
    )
    data_candidatura = models.DateTimeField(auto_now_add=True)
    aceitou_compartilhar_em = models.DateTimeField(null=True, blank=True)
    curriculo_snapshot = models.JSONField(
        null=True,
        blank=True,
        verbose_name='snapshot do currículo',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['vaga', 'candidata'],
                name='unique_candidatura_por_vaga',
            )
        ]
        ordering = ['-data_candidatura']
        verbose_name = 'candidatura'
        verbose_name_plural = 'candidaturas'

    def __str__(self):
        return f'{self.candidata.email} -> {self.vaga.titulo}'

    def clean(self):
        super().clean()
        if self.candidata_id and self.candidata.role != CustomUser.Role.EGRESSA:
            raise ValidationError(
                'Somente usuárias com perfil Egressa podem se candidatar.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
