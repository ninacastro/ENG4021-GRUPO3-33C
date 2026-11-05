import json
from datetime import date, datetime, timedelta
from urllib.request import urlopen

from django.utils import timezone

from .models import Aluno, Notificacao

API_URL = "https://brasilapi.com.br/api/feriados/v1/{ano}"


def buscar_feriados(ano):
    with urlopen(API_URL.format(ano=ano), timeout=10) as resposta:
        return json.load(resposta)


def criar_avisos_de_feriados(dias_antecedencia=14):
    """Cria o aviso 'não haverá aula' para todos os alunos, sem duplicar."""
    hoje = timezone.localdate()
    limite = hoje + timedelta(days=dias_antecedencia)

    feriados = []
    for ano in {hoje.year, limite.year}:
        feriados += buscar_feriados(ano)

    alunos = list(Aluno.objects.all())
    novos = []

    for feriado in feriados:
        data = datetime.strptime(feriado["date"], "%Y-%m-%d").date()

        # só feriados próximos e em dia de semana (sábado/domingo não têm aula mesmo)
        if not (hoje <= data <= limite) or data.weekday() >= 5:
            continue

        titulo = f"Sem aula: {feriado['name']} ({data:%d/%m})"[:100]
        ja_avisados = set(
            Notificacao.objects.filter(titulo=titulo).values_list("aluno_id", flat=True)
        )
        mensagem = (
            f"No dia {data:%d/%m/%Y} é feriado ({feriado['name']}). "
            "Não haverá aula."
        )
        novos += [
            Notificacao(aluno=a, titulo=titulo, mensagem=mensagem)
            for a in alunos
            if a.pk not in ja_avisados
        ]

    Notificacao.objects.bulk_create(novos)
    return len(novos)
