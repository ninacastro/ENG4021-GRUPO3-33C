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
    return render(request,"telaaulas.html")

def aula(request):
    return render(request,"aula.html")
