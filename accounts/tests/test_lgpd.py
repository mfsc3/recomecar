from datetime import timedelta
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from allauth.account.models import EmailAddress
from allauth.core import context
from allauth.socialaccount.models import SocialAccount, SocialLogin
from accounts.models import Curriculo
from allauth.socialaccount.internal.flows.signup import process_signup

from vagas.models import Candidatura, EmpresaProfile, Vaga


User = get_user_model()


class LgpdTests(TestCase):
    def setUp(self):
        cache.clear()

    def egressa_data(self, **overrides):
        data = {
            'first_name': 'Ana',
            'email': 'ana@example.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
            'aceitou_termo': 'on',
        }
        data.update(overrides)
        return data

    def test_public_signups_store_versioned_consent(self):
        before = timezone.now()
        self.client.post('/cadastro/egressa/', self.egressa_data())
        after = timezone.now()
        egressa = User.objects.get(email='ana@example.com')
        self.assertEqual(egressa.versao_termo, settings.TERMOS_VERSAO)
        self.assertTrue(before <= egressa.aceitou_termo_em <= after)

        self.client.post(
            '/cadastro/empresa/',
            {
                **self.egressa_data(email='empresa@example.com'),
                'razao_social': 'Empresa',
                'cnpj': '11.222.333/0001-81',
            },
        )
        empresa = User.objects.get(email='empresa@example.com')
        self.assertEqual(empresa.versao_termo, settings.TERMOS_VERSAO)
        self.assertIsNotNone(empresa.aceitou_termo_em)

    def test_social_signup_stores_versioned_consent(self):
        request = self.client.get('/login/').wsgi_request
        sociallogin = SocialLogin(
            user=User(email='google@example.com'),
            account=SocialAccount(provider='google', uid='google-1'),
            email_addresses=[
                EmailAddress(email='google@example.com', verified=True, primary=True),
            ],
        )
        with context.request_context(request):
            process_signup(request, sociallogin)
        user = User.objects.get(email='google@example.com')
        self.assertEqual(user.versao_termo, settings.TERMOS_VERSAO)
        self.assertIsNotNone(user.aceitou_termo_em)

    def test_consent_fields_from_post_are_ignored(self):
        before = timezone.now()
        self.client.post(
            '/cadastro/egressa/',
            self.egressa_data(
                aceitou_termo_em='2000-01-01T00:00:00Z',
                versao_termo='adulterada',
            ),
        )
        user = User.objects.get(email='ana@example.com')
        self.assertEqual(user.versao_termo, settings.TERMOS_VERSAO)
        self.assertNotEqual(user.versao_termo, 'adulterada')
        self.assertGreaterEqual(user.aceitou_termo_em, before)
        self.assertNotEqual(user.aceitou_termo_em.year, 2000)

    def test_application_records_sharing_consent_on_backend(self):
        company = User.objects.create_user(
            email='company@example.com',
            password='SenhaForte123!',
            role=User.Role.EMPRESA,
        )
        profile = EmpresaProfile.objects.create(
            user=company,
            cnpj='11222333000181',
            razao_social='Empresa',
            is_aprovada=True,
        )
        vaga = Vaga.objects.create(
            empresa=profile,
            titulo='Vaga',
            descricao='Descricao',
            requisitos='Requisitos',
        )
        candidate = User.objects.create_user(
            email='candidate@example.com',
            password='SenhaForte123!',
            role=User.Role.EGRESSA,
        )
        Curriculo.objects.create(user=candidate)
        self.client.force_login(candidate)
        before = timezone.now()
        response = self.client.post(
            f'/vagas/{vaga.pk}/candidatar/',
            {'aceitou_compartilhar_em': '2000-01-01'},
        )
        self.assertEqual(response.status_code, 302)
        application = Candidatura.objects.get(vaga=vaga, candidata=candidate)
        self.assertIsNotNone(application.aceitou_compartilhar_em)
        self.assertGreaterEqual(application.aceitou_compartilhar_em, before)
        self.assertNotEqual(application.aceitou_compartilhar_em.year, 2000)

    def test_social_data_is_cleared_after_login_and_signup(self):
        user = User.objects.create_user(
            email='social@example.com',
            password='SenhaForte123!',
            role=User.Role.EGRESSA,
        )
        account = SocialAccount.objects.create(
            user=user,
            provider='google',
            uid='uid-1',
            extra_data={'name': 'private'},
        )
        self.client.force_login(user)
        account.refresh_from_db()
        self.assertEqual(account.extra_data, {})
        self.assertEqual(account.uid, 'uid-1')

        request = self.client.get('/login/').wsgi_request
        sociallogin = SocialLogin(
            user=User(email='new-social@example.com'),
            account=SocialAccount(
                provider='google',
                uid='uid-2',
                extra_data={'name': 'private'},
            ),
            email_addresses=[
                EmailAddress(email='new-social@example.com', verified=True, primary=True),
            ],
        )
        with context.request_context(request):
            process_signup(request, sociallogin)
        account = SocialAccount.objects.get(uid='uid-2')
        self.assertEqual(account.extra_data, {})
        self.assertEqual(account.uid, 'uid-2')

    def test_admin_exposes_new_fields_as_read_only(self):
        from accounts.admin import CustomUserAdmin
        from django.contrib import admin

        registered = admin.site._registry[User]
        self.assertIsInstance(registered, CustomUserAdmin)
        self.assertIn('aceitou_termo_em', registered.readonly_fields)
        self.assertIn('versao_termo', registered.readonly_fields)
        from vagas.admin import CandidaturaAdmin
        self.assertIn(
            'aceitou_compartilhar_em',
            admin.site._registry[Candidatura].readonly_fields,
        )
