from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured, PermissionDenied

from .models import CustomUser


def _normalize_roles(roles):
    valid_roles = {role.value for role in CustomUser.Role}
    normalized = tuple(getattr(role, 'value', role) for role in roles)
    if not normalized or any(role not in valid_roles for role in normalized):
        raise ImproperlyConfigured('Configure pelo menos um papel válido.')
    return normalized


def role_required(*roles):
    allowed_roles = _normalize_roles(roles)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    settings.LOGIN_URL,
                    redirect_field_name='next',
                )
            if not request.user.is_active or request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


egressa_required = role_required(CustomUser.Role.EGRESSA)
empresa_required = role_required(CustomUser.Role.EMPRESA)
