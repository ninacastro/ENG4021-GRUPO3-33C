from django.shortcuts import render
from .models import *

def inicio(request):
    predios = Predio.objects.all()
    salas = Sala.objects.all()
    
    context = {
        'predios': predios,
        'salas': salas,
    }
    return render(request, "telainiciomelhorada.html", context)

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
    return render(request,"loginmelhorado.html")

def grade(request):
    aluno_atual = Aluno.objects.first()
    turmas_do_aluno = None
    if aluno_atual:
        turmas_do_aluno = aluno_atual.turmas.all()
    
    context = {
        'aluno': aluno_atual,
        'turmas': turmas_do_aluno,
    }
    return render(request,"telaaulas.html")

def aula(request):
    turma_especifica = Turma.objects.first()
    salas_da_turma = None
    if turma_especifica:
        salas_da_turma = turma_especifica.salas.all()
    
    context = {
        'turma': turma_especifica,
        'salas': salas_da_turma,
    }
    return render(request,"aula.html")

def deslogar(request):
    return render(request,"deslogar.html")


