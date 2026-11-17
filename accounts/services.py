from django.utils import timezone


def snapshot_curriculo(curriculo):
    """Retorna o estado atual do currículo como dados JSON-serializáveis."""
    return {
        'resumo': curriculo.resumo,
        'habilidades': curriculo.habilidades,
        'experiencias': [
            {
                'empresa_nome': experiencia.empresa_nome,
                'cargo': experiencia.cargo,
                'data_inicio': (
                    experiencia.data_inicio.isoformat()
                    if experiencia.data_inicio else None
                ),
                'data_fim': (
                    experiencia.data_fim.isoformat()
                    if experiencia.data_fim else None
                ),
                'descricao': experiencia.descricao,
            }
            for experiencia in curriculo.experiencias.all()
        ],
        'escolaridades': [
            {
                'instituicao': escolaridade.instituicao,
                'curso': escolaridade.curso,
                'nivel': escolaridade.nivel,
                'status': escolaridade.status,
                'ano_inicio': escolaridade.ano_inicio,
                'ano_conclusao': escolaridade.ano_conclusao,
            }
            for escolaridade in curriculo.escolaridades.all()
        ],
        'capturado_em': timezone.now().isoformat(),
    }
