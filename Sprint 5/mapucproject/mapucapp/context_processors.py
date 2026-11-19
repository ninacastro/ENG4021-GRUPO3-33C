from django.db.models import Max

from .models import Notificacao


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
