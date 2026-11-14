from django.urls import path

from .views import (
    CadastroEmpresaView,
    CadastroEgressaView,
    EmailLoginView,
    PainelView,
    PostOnlyLogoutView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', EmailLoginView.as_view(), name='login'),
    path('logout/', PostOnlyLogoutView.as_view(), name='logout'),
    path('cadastro/egressa/', CadastroEgressaView.as_view(), name='cadastro_egressa'),
    path('cadastro/empresa/', CadastroEmpresaView.as_view(), name='cadastro_empresa'),
    path('painel/', PainelView.as_view(), name='painel'),
]
