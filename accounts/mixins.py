from django.contrib.auth.mixins import AccessMixin

from .decorators import _normalize_roles
from .models import CustomUser


class RoleRequiredMixin(AccessMixin):
    allowed_roles = ()

    def has_required_role(self, request):
        allowed_roles = _normalize_roles(self.allowed_roles)
        return (
            request.user.is_authenticated
            and request.user.is_active
            and request.user.role in allowed_roles
        )

    def dispatch(self, request, *args, **kwargs):
        if not self.has_required_role(request):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class EgressaRequiredMixin(RoleRequiredMixin):
    allowed_roles = (CustomUser.Role.EGRESSA,)


class EmpresaRequiredMixin(RoleRequiredMixin):
    allowed_roles = (CustomUser.Role.EMPRESA,)
