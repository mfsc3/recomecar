from django.test import TestCase

from accounts.models import CustomUser
from vagas.models import EmpresaProfile, Vaga


class VagaTestCase(TestCase):
    def create_empresa(self, email, approved=False):
        user = CustomUser.objects.create_user(
            email=email,
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )
        number = EmpresaProfile.objects.count() + 181
        return EmpresaProfile.objects.create(
            user=user,
            cnpj=f'11222333000{number}',
            razao_social=f'Empresa {number}',
            is_aprovada=approved,
        )

    def create_vaga(self, empresa, titulo='Vaga de teste', ativa=True):
        return Vaga.objects.create(
            empresa=empresa,
            titulo=titulo,
            descricao='Atividades da função.',
            requisitos='Competências da função.',
            ativa=ativa,
        )

    def create_egressa(self, email='egressa@example.com'):
        return CustomUser.objects.create_user(
            email=email,
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )
