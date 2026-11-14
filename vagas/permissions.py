from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from accounts.decorators import empresa_required
from accounts.mixins import EmpresaRequiredMixin


class EmpresaAprovadaRequiredMixin(EmpresaRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not self.has_required_role(request):
            return super().dispatch(request, *args, **kwargs)
        self.empresa = getattr(request.user, 'empresa_profile', None)
        if self.empresa is None:
            raise PermissionDenied
        if not self.empresa.is_aprovada:
            messages.warning(
                request,
                'Sua empresa ainda não foi aprovada pelo administrador.',
            )
            return redirect('accounts:painel')
        return super().dispatch(request, *args, **kwargs)


def empresa_aprovada_required(view_func):
    @empresa_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        empresa = getattr(request.user, 'empresa_profile', None)
        if empresa is None:
            raise PermissionDenied
        if not empresa.is_aprovada:
            messages.warning(
                request,
                'Sua empresa ainda não foi aprovada pelo administrador.',
            )
            return redirect('accounts:painel')
        return view_func(request, *args, **kwargs)

    return wrapped


class EmpresaComPerfilMixin(EmpresaRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not self.has_required_role(request):
            return super().dispatch(request, *args, **kwargs)
        self.empresa = getattr(request.user, 'empresa_profile', None)
        if self.empresa is None:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
