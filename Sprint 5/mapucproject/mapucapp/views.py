from django.shortcuts import render

def inicio(request):
    return render(request,"telainicio.html")

def bibliotecas(request):
    return render(request,"bibliotecas.html")
