import re
import shutil
from io import BytesIO
from tempfile import mkdtemp

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from allauth.account.models import EmailAddress
from vagas.models import Candidatura, EmpresaProfile, Vaga
from vitrine.models import ProdutoServico


User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class FluxoPontaAPontaTests(TestCase):
    def setUp(self):
        cache.clear()
        Site.objects.update_or_create(
            id=1,
            defaults={'domain': 'testserver', 'name': 'Recomeçar'},
        )
        self.media_root = mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.company_client = self.client_class()
        self.egressa_client = self.client_class()
        self.admin_client = self.client_class()

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)
        super().tearDown()

    def egressa_data(self, email='ana@example.com', **overrides):
        data = {
            'first_name': 'Ana',
            'email': email,
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
            'aceitou_termo': 'on',
        }
        data.update(overrides)
        return data

    def empresa_data(self):
        return self.egressa_data(
            email='empresa@example.com',
            first_name='Responsável',
            razao_social='Empresa Teste',
            cnpj='11.222.333/0001-81',
        )

    def confirmation_path(self):
        match = re.search(
            r'https?://[^/]+(/accounts/confirm-email/[^/\s]+/)',
            mail.outbox[-1].body,
        )
        self.assertIsNotNone(match)
        return match.group(1)

    def confirm_signup(self, client, path):
        self.assertEqual(client.get(path).status_code, 200)
        response = client.post(path)
        self.assertEqual(response.status_code, 302)

    def login(self, client, email):
        response = client.post(
            '/login/',
            {'username': email, 'password': 'SenhaForte123!'},
        )
        self.assertRedirects(response, '/painel/')

    def image_upload(self):
        output = BytesIO()
        Image.new('RGB', (40, 40), 'white').save(output, format='JPEG')
        return SimpleUploadedFile(
            'produto.jpg',
            output.getvalue(),
            content_type='image/jpeg',
        )

    def test_fluxo_empresa_egressa_e_candidatura(self):
        mail.outbox.clear()
        response = self.company_client.post(
            '/cadastro/empresa/',
            self.empresa_data(),
        )
        self.assertRedirects(response, '/login/')
        self.assertEqual(len(mail.outbox), 1)
        company_path = self.confirmation_path()
        company = User.objects.get(email='empresa@example.com')
        self.assertFalse(company.is_active)

        before_confirmation = self.company_client.post(
            '/login/',
            {'username': company.email, 'password': 'SenhaForte123!'},
        )
        self.assertContains(before_confirmation, 'E-mail ou senha incorretos.')
        self.assertNotIn('_auth_user_id', self.company_client.session)

        self.confirm_signup(self.company_client, company_path)
        company.refresh_from_db()
        self.assertTrue(company.is_active)
        self.login(self.company_client, company.email)
        self.assertContains(self.company_client.get('/painel/'), 'Aguardando aprovação')

        self.assertRedirects(
            self.company_client.get('/vagas/minhas/nova/'),
            '/painel/',
        )

        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='SenhaForte123!',
        )
        self.admin_client.force_login(admin)
        profile = EmpresaProfile.objects.get(user=company)
        approval = self.admin_client.post(
            reverse('admin:vagas_empresaprofile_changelist'),
            {
                'action': 'aprovar_empresas',
                '_selected_action': [profile.pk],
            },
        )
        self.assertEqual(approval.status_code, 302)
        profile.refresh_from_db()
        self.assertTrue(profile.is_aprovada)

        self.assertEqual(self.company_client.get('/vagas/minhas/nova/').status_code, 200)
        response = self.company_client.post(
            '/vagas/minhas/nova/',
            {
                'titulo': 'Vaga de atendimento',
                'descricao': 'Atividades de atendimento.',
                'requisitos': 'Boa comunicação.',
                'ativa': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        vaga = Vaga.objects.get(titulo='Vaga de atendimento')
        self.assertContains(self.client.get('/vagas/'), vaga.titulo)

        mail.outbox.clear()
        response = self.egressa_client.post(
            '/cadastro/egressa/',
            self.egressa_data(),
        )
        self.assertRedirects(response, '/login/')
        egressa_path = self.confirmation_path()
        self.confirm_signup(self.egressa_client, egressa_path)
        self.login(self.egressa_client, 'ana@example.com')
        candidate = User.objects.get(email='ana@example.com')

        application = self.egressa_client.post(
            reverse('vagas:candidatar', args=[vaga.pk]),
        )
        self.assertEqual(application.status_code, 302)
        candidatura = Candidatura.objects.get(vaga=vaga, candidata=candidate)
        self.assertIsNotNone(candidatura.aceitou_compartilhar_em)

        response = self.company_client.get(
            reverse('vagas:minha_detalhe', args=[vaga.pk]),
        )
        self.assertContains(response, candidate.email)
        self.assertNotContains(response, candidate.first_name)

    def test_fluxo_egressa_vitrine_e_segregacao(self):
        mail.outbox.clear()
        response = self.egressa_client.post(
            '/cadastro/egressa/',
            self.egressa_data(email='vitrine@example.com'),
        )
        self.assertRedirects(response, '/login/')
        path = self.confirmation_path()
        self.confirm_signup(self.egressa_client, path)
        self.login(self.egressa_client, 'vitrine@example.com')

        response = self.egressa_client.get('/vitrine/minha/novo/')
        self.assertEqual(response.status_code, 200)
        response = self.egressa_client.post(
            '/vitrine/minha/novo/',
            {
                'nome_exibicao': 'Ateliê Sol',
                'titulo': 'Bolos artesanais',
                'descricao': 'Bolos feitos sob encomenda.',
                'categoria': 'PRODUTO',
                'contato': 'contato público',
                'is_ativo': 'on',
                'aceito_publicar': 'on',
                'imagem': self.image_upload(),
            },
        )
        self.assertEqual(response.status_code, 302)
        owner = User.objects.get(email='vitrine@example.com')
        item = ProdutoServico.objects.get(owner=owner)
        public = self.client.get('/vitrine/')
        self.assertContains(public, item.titulo)
        self.assertNotContains(public, owner.email)
        self.assertNotContains(public, owner.first_name)

        company = User.objects.create_user(
            email='empresa-vitrine@example.com',
            password='SenhaForte123!',
            role=User.Role.EMPRESA,
        )
        self.client.force_login(company)
        self.assertEqual(self.client.get('/vitrine/minha/novo/').status_code, 403)
