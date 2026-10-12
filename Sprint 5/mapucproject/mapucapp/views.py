from django.shortcuts import render

def inicio(request):
    return render(request,"telainicio-melhorada.html")

def bibliotecas(request):
    return render(request,"bibliotecas.html")

def perfil(request):
    return render(request,"telaperfilmelhorado.html")

def login(request):
    return render(request,"loginmelhorado.html")

def grade(request):
    return render(request,"telaaulas.html")

def aula(request):
    return render(request,"aula.html")
