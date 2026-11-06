import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen

from django.core.cache import cache
from django.utils import timezone

from .models import Aluno, Notificacao

API_URL = "https://brasilapi.com.br/api/feriados/v1/{ano}"
CAMPUS_TIME_ZONE = ZoneInfo("America/Sao_Paulo")
FERIADOS_CACHE_TTL = 60 * 60 * 12


def buscar_feriados(ano):
    cache_key = f"feriados_nacionais_{ano}"
    feriados = cache.get(cache_key)
    if feriados is not None:
        return feriados

    requisicao = Request(
        API_URL.format(ano=ano),
        headers={
            "User-Agent": "Mozilla/5.0 MaPUC/1.0",
            "Accept": "application/json",
        },
    )
    with urlopen(requisicao, timeout=10) as resposta:
        feriados = json.load(resposta)

    if not isinstance(feriados, list):
        raise ValueError("A API não retornou uma lista de feriados.")

    cache.set(cache_key, feriados, FERIADOS_CACHE_TTL)
    return feriados


def obter_feriados_proximos(dias_antecedencia=30, hoje=None):
    """Retorna feriados nacionais em dias úteis dentro do período próximo."""
    hoje = hoje or timezone.localdate(timezone=CAMPUS_TIME_ZONE)
    limite = hoje + timedelta(days=dias_antecedencia)

    feriados_do_ano = []
    for ano in {hoje.year, limite.year}:
        feriados_do_ano.extend(buscar_feriados(ano))

    proximos = []
    dias_semana = (
        "segunda-feira",
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "sábado",
        "domingo",
    )

    for feriado in feriados_do_ano:
        if (
            not isinstance(feriado, dict)
            or not isinstance(feriado.get("date"), str)
            or not isinstance(feriado.get("name"), str)
        ):
            raise ValueError("A API retornou um feriado em formato inválido.")
        data = datetime.strptime(feriado["date"], "%Y-%m-%d").date()

        if not (hoje <= data <= limite) or data.weekday() >= 5:
            continue

        proximos.append({
            "nome": feriado["name"],
            "data": data,
            "data_formatada": data.strftime("%d/%m/%Y"),
            "dia_semana": dias_semana[data.weekday()],
        })

    return sorted(proximos, key=lambda feriado: feriado["data"])


def criar_avisos_de_feriados(dias_antecedencia=30, hoje=None):
    """Cria avisos para os próximos feriados em dias úteis, sem duplicar."""
    feriados = obter_feriados_proximos(dias_antecedencia, hoje=hoje)
    alunos = list(Aluno.objects.all())
    titulos = [
        f"Sem aula: {feriado['nome']} ({feriado['data']:%d/%m/%Y})"[:100]
        for feriado in feriados
    ]
    avisos_existentes = set(
        Notificacao.objects.filter(titulo__in=titulos).values_list("aluno_id", "titulo")
    )
    novos = []

    for feriado, titulo in zip(feriados, titulos):
        data = feriado["data"]
        mensagem = (
            f"No dia {data:%d/%m/%Y} é feriado ({feriado['nome']}). "
            "Não haverá aula."
        )
        novos += [
            Notificacao(aluno=a, titulo=titulo, mensagem=mensagem)
            for a in alunos
            if (a.pk, titulo) not in avisos_existentes
        ]

    Notificacao.objects.bulk_create(novos)
    return len(novos)
