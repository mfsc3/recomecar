from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.views import View

from accounts.decorators import role_required
from accounts.mixins import RoleRequiredMixin
from accounts.models import CustomUser


class DecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='egressa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EGRESSA,
        )

    def test_anonymous_is_redirected(self):
        @role_required(CustomUser.Role.EMPRESA)
        def view(request):
            return HttpResponse('ok')

        request = self.factory.get('/privado/?pagina=2')
        request.user = AnonymousUser()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/login/?next=/privado/%3Fpagina%3D2')

    def test_wrong_role_is_forbidden(self):
        @role_required(CustomUser.Role.EMPRESA)
        def view(request):
            return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_allowed_role_runs_view(self):
        @role_required(CustomUser.Role.EGRESSA)
        def view(request):
            return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        self.assertEqual(view(request).status_code, 200)

    def test_multiple_roles_are_supported(self):
        @role_required(CustomUser.Role.EGRESSA, CustomUser.Role.EMPRESA)
        def view(request):
            return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        self.assertEqual(view(request).status_code, 200)

    def test_admin_has_no_implicit_bypass(self):
        self.user.role = CustomUser.Role.ADMIN
        self.user.is_superuser = True
        self.user.save(update_fields=['role', 'is_superuser'])

        @role_required(CustomUser.Role.EMPRESA)
        def view(request):
            return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_inactive_user_is_forbidden(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])

        @role_required(CustomUser.Role.EGRESSA)
        def view(request):
            return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_invalid_decorator_configuration_fails_immediately(self):
        with self.assertRaises(ImproperlyConfigured):
            role_required()
        with self.assertRaises(ImproperlyConfigured):
            role_required('UNKNOWN')


class RoleRequiredMixinTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='empresa@example.com',
            password='SenhaForte123!',
            role=CustomUser.Role.EMPRESA,
        )

    def test_anonymous_is_redirected(self):
        class ProtectedView(RoleRequiredMixin, View):
            allowed_roles = (CustomUser.Role.EMPRESA,)

            def get(self, request):
                return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = AnonymousUser()
        response = ProtectedView.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_wrong_role_is_forbidden(self):
        class ProtectedView(RoleRequiredMixin, View):
            allowed_roles = (CustomUser.Role.EGRESSA,)

            def get(self, request):
                return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            ProtectedView.as_view()(request)

    def test_allowed_role_runs_view(self):
        class ProtectedView(RoleRequiredMixin, View):
            allowed_roles = (CustomUser.Role.EMPRESA,)

            def get(self, request):
                return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        self.assertEqual(ProtectedView.as_view()(request).status_code, 200)

    def test_multiple_roles_are_supported(self):
        class ProtectedView(RoleRequiredMixin, View):
            allowed_roles = (CustomUser.Role.EGRESSA, CustomUser.Role.EMPRESA)

            def get(self, request):
                return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        self.assertEqual(ProtectedView.as_view()(request).status_code, 200)

    def test_inactive_user_is_forbidden(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])

        class ProtectedView(RoleRequiredMixin, View):
            allowed_roles = (CustomUser.Role.EMPRESA,)

            def get(self, request):
                return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            ProtectedView.as_view()(request)

    def test_admin_has_no_implicit_bypass(self):
        self.user.role = CustomUser.Role.ADMIN
        self.user.is_superuser = True
        self.user.save(update_fields=['role', 'is_superuser'])

        class ProtectedView(RoleRequiredMixin, View):
            allowed_roles = (CustomUser.Role.EMPRESA,)

            def get(self, request):
                return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            ProtectedView.as_view()(request)

    def test_empty_configuration_fails_closed(self):
        class ProtectedView(RoleRequiredMixin, View):
            def get(self, request):
                return HttpResponse('ok')

        request = self.factory.get('/privado/')
        request.user = self.user
        with self.assertRaises(ImproperlyConfigured):
            ProtectedView.as_view()(request)
