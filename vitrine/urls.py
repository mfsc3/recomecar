from django.urls import path

from .views import (
    MinhaVitrineView,
    ProdutoCreateView,
    ProdutoDeleteView,
    ProdutoUpdateView,
    VitrineDetalheView,
    VitrineListaView,
)

app_name = 'vitrine'

urlpatterns = [
    path('', VitrineListaView.as_view(), name='lista'),
    path('<int:pk>/', VitrineDetalheView.as_view(), name='detalhe'),
    path('minha/', MinhaVitrineView.as_view(), name='minha'),
    path('minha/novo/', ProdutoCreateView.as_view(), name='criar'),
    path('minha/<int:pk>/editar/', ProdutoUpdateView.as_view(), name='editar'),
    path('minha/<int:pk>/excluir/', ProdutoDeleteView.as_view(), name='excluir'),
]
