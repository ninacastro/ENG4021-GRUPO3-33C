from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def home(request):
    return render(request, 'avisos.html')

def perfil(request):
    return render(request, 'perfil.html')

def horario(request):
    return render(request, 'horario.html')