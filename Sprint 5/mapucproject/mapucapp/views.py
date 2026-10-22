from django.shortcuts import render
from django.db.models import Q
from .models import *

def inicio(request):
    busca = request.GET.get('busca', '').strip()

    predios = Predio.objects.none()
    salas = Sala.objects.none()

    if busca:
        predios = Predio.objects.filter(
            Q(nome__icontains=busca) |
            Q(sigla_codigo__icontains=busca)
        )
        salas = Sala.objects.select_related('predio', 'andar').filter(
            Q(codigo_sala__icontains=busca) |
            Q(nome_exibicao__icontains=busca) |
            Q(predio__nome__icontains=busca) |
            Q(predio__sigla_codigo__icontains=busca)
        )

    context = {
        'busca': busca,
        'predios': predios,
        'salas': salas,
    }
    return render(request, "telainiciomelhorado.html", context)


def bibliotecas(request):
    bibliotecas = Sala.objects.filter(tipo_sala__icontains="Biblioteca")

    context = {
        'bibliotecas': bibliotecas,
    }
    return render(request, "bibliotecas.html", context)


def perfil(request):
    aluno = Aluno.objects.first()
    turmas = None
    if aluno:
        turmas = aluno.turmas.all()

    context = {
        'aluno': aluno,
        'turmas': turmas,
    }
    return render(request, "telaperfilmelhorado.html", context)


def login(request):
    return render(request, "loginmelhorado.html")


def grade(request):
    aluno_atual = Aluno.objects.first()
    turmas_do_aluno = None
    if aluno_atual:
        turmas_do_aluno = aluno_atual.turmas.all()

    context = {
        'aluno': aluno_atual,
        'turmas': turmas_do_aluno,
    }
    return render(request, "telaaulas.html", context)


def aula(request):
    turma_especifica = Turma.objects.first()
    salas_da_turma = None
    if turma_especifica:
        salas_da_turma = turma_especifica.salas.all()

    context = {
        'turma': turma_especifica,
        'salas': salas_da_turma,
    }
    return render(request, "aula.html", context)


def deslogar(request):
    aluno = Aluno.objects.first()
    iniciais = ""
    if aluno:
        partes = aluno.nome.split()
        iniciais = (partes[0][0] + partes[-1][0]).upper()

    context = {
        'aluno': aluno,
        'iniciais': iniciais,
    }
    return render(request, "deslogar.html", context)


def dados(request):
    return render(request, "dados.html")


def notificacoes(request):
    return render(request, 'notificacoesmelhorado.html')


def rota(request):
    return render(request, 'telarota.html')



