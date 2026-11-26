from django.db.models import Max

from .models import Aluno, Notificacao


def iniciais_do_nome(nome):
    """Primeira letra do primeiro nome + primeira letra do último nome."""
    partes = (nome or '').split()
    if not partes:
        return '?'
    if len(partes) == 1:
        return partes[0][0].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def aluno_iniciais(request):
    aluno_id = request.session.get('aluno_id')
    if aluno_id is None:
        return {'aluno_iniciais': None}

    nome = (
        Aluno.objects.filter(pk=aluno_id)
        .values_list('nome', flat=True)
        .first()
    )
    return {'aluno_iniciais': iniciais_do_nome(nome) if nome else None}


def notificacoes_popup(request):
    aluno_id = request.session.get('aluno_id')
    if aluno_id is None:
        return {'notificacoes_popup': None}

    cursor = Notificacao.objects.aggregate(
        ultimo_id=Max('id_notificacao'),
    )['ultimo_id'] or 0
    return {
        'notificacoes_popup': {
            'aluno_id': aluno_id,
            'cursor': cursor,
        },
    }
