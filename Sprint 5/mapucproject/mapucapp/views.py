from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Q
from .models import Predio, Sala


# Tela de início
def inicio(request):
    busca = request.GET.get('busca', '')

    predios = Predio.objects.none()
    salas = Sala.objects.none()

    if busca:
        predios = Predio.objects.filter(
            Q(nome__icontains=busca) |
            Q(sigla_codigo__icontains=busca)
        )

        salas = Sala.objects.filter(
            Q(codigo_sala__icontains=busca) |
            Q(nome_exibicao__icontains=busca) |
            Q(predio__nome__icontains=busca) |
            Q(predio__sigla_codigo__icontains=busca)
        )

    return render(request, "telainicio-melhorada.html", {
        "busca": busca,
        "predios": predios,
        "salas": salas
    })


def inicio(request):
    return render(request,"telainicio-melhorada.html")

def bibliotecas(request):
    return render(request,"bibliotecas.html")

def perfil(request):
    return render(request,"telaperfilmelhorado.html")

def login(request):
    return render(request,"loginmelhorado.html")

def deslogar(request):
    return render(request, "deslogar.html")