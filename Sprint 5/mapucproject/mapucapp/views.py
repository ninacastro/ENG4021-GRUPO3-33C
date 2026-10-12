from django.shortcuts import render

def inicio(request):
    return render(request,"telainicio.html")

def bibliotecas(request):
    return render(request,"bibliotecas.html")

def perfil(request):
    return render(request,"telaperfilmelhorado.html")

def login(request):
    return render(request,"loginmelhorado.html")