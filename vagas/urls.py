from django.urls import path

from .views import (
    CandidatarView,
    CandidataCurriculoView,
    EmpresaProfileUpdateView,
    MinhaVagaDetailView,
    MinhasVagasView,
    VagaCreateView,
    VagaDeleteView,
    VagaDetalhePublicaView,
    VagaListaPublicaView,
    VagaUpdateView,
)

app_name = 'vagas'

urlpatterns = [
    path('', VagaListaPublicaView.as_view(), name='lista'),
    path('<int:pk>/', VagaDetalhePublicaView.as_view(), name='detalhe_publica'),
    path('<int:pk>/candidatar/', CandidatarView.as_view(), name='candidatar'),
    path('minhas/', MinhasVagasView.as_view(), name='minhas'),
    path('minhas/nova/', VagaCreateView.as_view(), name='criar'),
    path('minhas/<int:pk>/', MinhaVagaDetailView.as_view(), name='minha_detalhe'),
    path('minhas/<int:pk>/editar/', VagaUpdateView.as_view(), name='editar'),
    path('minhas/<int:pk>/excluir/', VagaDeleteView.as_view(), name='excluir'),
    path(
        'minha-empresa/editar/',
        EmpresaProfileUpdateView.as_view(),
        name='empresa_editar',
    ),
    path(
        'minhas/<int:vaga_pk>/candidaturas/<int:pk>/',
        CandidataCurriculoView.as_view(),
        name='candidata_curriculo',
    ),
]
