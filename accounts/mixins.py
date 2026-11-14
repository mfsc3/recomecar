from django.contrib.auth.mixins import AccessMixin

from .decorators import _normalize_roles
from .models import CustomUser


class RoleRequiredMixin(AccessMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        allowed_roles = _normalize_roles(self.allowed_roles)
        if (
            not request.user.is_authenticated
            or not request.user.is_active
            or request.user.role not in allowed_roles
        ):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class EgressaRequiredMixin(RoleRequiredMixin):
    allowed_roles = (CustomUser.Role.EGRESSA,)


class EmpresaRequiredMixin(RoleRequiredMixin):
    allowed_roles = (CustomUser.Role.EMPRESA,)
